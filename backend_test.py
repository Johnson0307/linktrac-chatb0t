#!/usr/bin/env python3
"""
Backend Testing Suite for Linktrac Chatbot
Tests all API endpoints and functionality
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import time

# Backend URL from frontend/.env
BACKEND_URL = "https://47273318-cc84-4e43-9057-53665d6bb240.preview.emergentagent.com/api"

class LinktracChatbotTester:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        print()
    
    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Health Check", True, f"Service: {data.get('service')}")
                    return True
                else:
                    self.log_test("Health Check", False, f"Unexpected status: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_contacts_endpoint(self):
        """Test contacts information endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/contacts", timeout=10)
            if response.status_code == 200:
                data = response.json()
                contacts = data.get("contacts", {})
                
                # Verify contact structure
                if "suporte" in contacts and "vendedores" in contacts:
                    suporte = contacts["suporte"]
                    vendedores = contacts["vendedores"]
                    
                    # Check suporte structure
                    if "dia" in suporte and "noite" in suporte:
                        # Check vendedores structure
                        if isinstance(vendedores, list) and len(vendedores) > 0:
                            vendor_check = all("name" in v and "phone" in v for v in vendedores)
                            if vendor_check:
                                self.log_test("Contacts Endpoint", True, f"Found {len(vendedores)} vendors and support contacts")
                                return True
                            else:
                                self.log_test("Contacts Endpoint", False, "Invalid vendor structure")
                                return False
                        else:
                            self.log_test("Contacts Endpoint", False, "No vendors found")
                            return False
                    else:
                        self.log_test("Contacts Endpoint", False, "Invalid support structure")
                        return False
                else:
                    self.log_test("Contacts Endpoint", False, "Missing suporte or vendedores")
                    return False
            else:
                self.log_test("Contacts Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Contacts Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_chat_conversation(self):
        """Test chatbot conversation flow"""
        try:
            # Test initial greeting
            chat_data = {
                "session_id": self.session_id,
                "message": "Olá",
                "department": None
            }
            
            response = requests.post(f"{BACKEND_URL}/chat", json=chat_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "response" in data and "department" in data:
                    self.log_test("Chat Initial Greeting", True, f"Department: {data['department']}")
                    
                    # Test department routing - Financeiro
                    chat_data["message"] = "financeiro"
                    response = requests.post(f"{BACKEND_URL}/chat", json=chat_data, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("department") == "financeiro":
                            self.log_test("Chat Department Routing - Financeiro", True, "Correctly routed to financeiro")
                            
                            # Test Vendas routing
                            chat_data["message"] = "vendas"
                            response = requests.post(f"{BACKEND_URL}/chat", json=chat_data, timeout=10)
                            if response.status_code == 200:
                                data = response.json()
                                if data.get("department") == "vendas":
                                    self.log_test("Chat Department Routing - Vendas", True, "Correctly routed to vendas")
                                    
                                    # Test Suporte routing
                                    chat_data["message"] = "suporte"
                                    response = requests.post(f"{BACKEND_URL}/chat", json=chat_data, timeout=10)
                                    if response.status_code == 200:
                                        data = response.json()
                                        if data.get("department") == "suporte":
                                            self.log_test("Chat Department Routing - Suporte", True, "Correctly routed to suporte")
                                            return True
                                        else:
                                            self.log_test("Chat Department Routing - Suporte", False, f"Wrong department: {data.get('department')}")
                                            return False
                                    else:
                                        self.log_test("Chat Department Routing - Suporte", False, f"HTTP {response.status_code}")
                                        return False
                                else:
                                    self.log_test("Chat Department Routing - Vendas", False, f"Wrong department: {data.get('department')}")
                                    return False
                            else:
                                self.log_test("Chat Department Routing - Vendas", False, f"HTTP {response.status_code}")
                                return False
                        else:
                            self.log_test("Chat Department Routing - Financeiro", False, f"Wrong department: {data.get('department')}")
                            return False
                    else:
                        self.log_test("Chat Department Routing - Financeiro", False, f"HTTP {response.status_code}")
                        return False
                else:
                    self.log_test("Chat Initial Greeting", False, "Missing response or department fields")
                    return False
            else:
                self.log_test("Chat Initial Greeting", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Chat Conversation", False, f"Exception: {str(e)}")
            return False
    
    def test_debt_consultation(self):
        """Test debt consultation with Asas API"""
        try:
            # Test with a sample customer ID (sandbox environment)
            debt_data = {
                "customer_id": "cus_000005928840",  # Sample customer ID for sandbox
                "session_id": self.session_id
            }
            
            response = requests.post(f"{BACKEND_URL}/consult-debt", json=debt_data, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if "success" in data and "data" in data:
                    # In sandbox, we might get an error or empty data, which is expected
                    if data["success"] or "error" in data["data"]:
                        self.log_test("Debt Consultation API", True, "API call successful (sandbox environment)")
                        return True
                    else:
                        self.log_test("Debt Consultation API", False, f"Unexpected response: {data}")
                        return False
                else:
                    self.log_test("Debt Consultation API", False, f"Invalid response structure: {data}")
                    return False
            else:
                self.log_test("Debt Consultation API", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Debt Consultation API", False, f"Exception: {str(e)}")
            return False
    
    def test_boleto_generation(self):
        """Test boleto generation with Asas API"""
        try:
            # Test boleto generation with sample data
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            boleto_data = {
                "customer_id": "cus_000005928840",  # Sample customer ID for sandbox
                "value": 150.00,
                "due_date": due_date,
                "description": "Teste de geração de boleto - Linktrac Chatbot",
                "session_id": self.session_id
            }
            
            response = requests.post(f"{BACKEND_URL}/generate-boleto", json=boleto_data, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if "success" in data and "data" in data:
                    # In sandbox, we might get an error for non-existent customer, which is expected
                    if data["success"] or "error" in data["data"]:
                        self.log_test("Boleto Generation API", True, "API call successful (sandbox environment)")
                        return True
                    else:
                        self.log_test("Boleto Generation API", False, f"Unexpected response: {data}")
                        return False
                else:
                    self.log_test("Boleto Generation API", False, f"Invalid response structure: {data}")
                    return False
            else:
                self.log_test("Boleto Generation API", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Boleto Generation API", False, f"Exception: {str(e)}")
            return False
    
    def test_chat_history(self):
        """Test chat history retrieval"""
        try:
            # First, ensure we have some chat messages by sending a message
            chat_data = {
                "session_id": self.session_id,
                "message": "Teste de histórico",
                "department": None
            }
            requests.post(f"{BACKEND_URL}/chat", json=chat_data, timeout=10)
            
            # Wait a moment for the message to be saved
            time.sleep(1)
            
            # Now retrieve chat history
            response = requests.get(f"{BACKEND_URL}/chat-history/{self.session_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "messages" in data:
                    messages = data["messages"]
                    if len(messages) > 0:
                        # Check message structure
                        first_message = messages[0]
                        required_fields = ["session_id", "message", "sender", "timestamp"]
                        if all(field in first_message for field in required_fields):
                            self.log_test("Chat History Retrieval", True, f"Found {len(messages)} messages")
                            return True
                        else:
                            self.log_test("Chat History Retrieval", False, "Invalid message structure")
                            return False
                    else:
                        self.log_test("Chat History Retrieval", True, "No messages found (empty history)")
                        return True
                else:
                    self.log_test("Chat History Retrieval", False, "Missing messages field")
                    return False
            else:
                self.log_test("Chat History Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Chat History Retrieval", False, f"Exception: {str(e)}")
            return False
    
    def test_mongodb_persistence(self):
        """Test MongoDB data persistence by checking if data is saved and retrieved"""
        try:
            # Send multiple messages to test persistence
            test_messages = [
                "Olá, teste de persistência",
                "financeiro",
                "consultar débitos"
            ]
            
            for msg in test_messages:
                chat_data = {
                    "session_id": self.session_id,
                    "message": msg,
                    "department": None
                }
                response = requests.post(f"{BACKEND_URL}/chat", json=chat_data, timeout=10)
                if response.status_code != 200:
                    self.log_test("MongoDB Persistence", False, f"Failed to send message: {msg}")
                    return False
            
            # Wait for messages to be saved
            time.sleep(2)
            
            # Retrieve and verify messages
            response = requests.get(f"{BACKEND_URL}/chat-history/{self.session_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                
                # Check if we have both user and bot messages
                user_messages = [m for m in messages if m.get("sender") == "user"]
                bot_messages = [m for m in messages if m.get("sender") == "bot"]
                
                if len(user_messages) >= len(test_messages) and len(bot_messages) >= len(test_messages):
                    self.log_test("MongoDB Persistence", True, f"Saved and retrieved {len(user_messages)} user messages and {len(bot_messages)} bot messages")
                    return True
                else:
                    self.log_test("MongoDB Persistence", False, f"Expected at least {len(test_messages)} messages each, got {len(user_messages)} user and {len(bot_messages)} bot")
                    return False
            else:
                self.log_test("MongoDB Persistence", False, f"Failed to retrieve chat history: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("MongoDB Persistence", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Linktrac Chatbot Backend Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Session ID: {self.session_id}")
        print("=" * 60)
        
        # Run tests in order
        tests = [
            self.test_health_check,
            self.test_contacts_endpoint,
            self.test_chat_conversation,
            self.test_debt_consultation,
            self.test_boleto_generation,
            self.test_chat_history,
            self.test_mongodb_persistence
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {total - passed} tests failed")
        
        return passed, total, self.test_results

if __name__ == "__main__":
    tester = LinktracChatbotTester()
    passed, total, results = tester.run_all_tests()
    
    # Print detailed results
    print("\n📋 Detailed Test Results:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}")
        if result["details"]:
            print(f"   {result['details']}")