import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId] = useState(() => 'session_' + Date.now());
  const [isLoading, setIsLoading] = useState(false);
  const [currentDepartment, setCurrentDepartment] = useState('geral');
  const [showDebtForm, setShowDebtForm] = useState(false);
  const [showBoletoForm, setShowBoletoForm] = useState(false);
  const [customerInfo, setCustomerInfo] = useState({
    customerId: '',
    value: '',
    dueDate: '',
    description: ''
  });
  const messagesEndRef = useRef(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    // Send initial greeting
    sendInitialMessage();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendInitialMessage = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: 'início',
          department: currentDepartment
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setMessages([{
          id: Date.now(),
          text: data.response,
          sender: 'bot',
          timestamp: new Date(),
          options: data.options,
          contactInfo: data.contact_info,
          department: data.department
        }]);
        setCurrentDepartment(data.department);
      }
    } catch (error) {
      console.error('Error sending initial message:', error);
    }
  };

  const sendMessage = async (messageText = inputMessage) => {
    if (!messageText.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: messageText,
          department: currentDepartment
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const botMessage = {
          id: Date.now() + 1,
          text: data.response,
          sender: 'bot',
          timestamp: new Date(),
          options: data.options,
          contactInfo: data.contact_info,
          department: data.department
        };

        setMessages(prev => [...prev, botMessage]);
        setCurrentDepartment(data.department);

        // Show forms based on department
        if (data.department === 'financeiro_consulta') {
          setShowDebtForm(true);
          setShowBoletoForm(false);
        } else if (data.department === 'financeiro_boleto') {
          setShowBoletoForm(true);
          setShowDebtForm(false);
        } else {
          setShowDebtForm(false);
          setShowBoletoForm(false);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Desculpe, ocorreu um erro. Tente novamente.',
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDebtConsultation = async () => {
    if (!customerInfo.customerId.trim()) {
      alert('Por favor, informe o ID do cliente');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/consult-debt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_id: customerInfo.customerId,
          session_id: sessionId
        }),
      });

      if (response.ok) {
        const data = await response.json();
        let resultText = '📊 **Resultado da Consulta de Débitos**\n\n';
        
        if (data.data.error) {
          resultText += `❌ ${data.data.error}`;
        } else if (data.data.data && data.data.data.length > 0) {
          resultText += `✅ Encontrados ${data.data.data.length} débito(s):\n\n`;
          data.data.data.forEach((debt, index) => {
            resultText += `**Débito ${index + 1}:**\n`;
            resultText += `• Valor: R$ ${debt.value}\n`;
            resultText += `• Vencimento: ${debt.dueDate}\n`;
            resultText += `• Status: ${debt.status}\n\n`;
          });
        } else {
          resultText += '✅ Nenhum débito encontrado para este cliente.';
        }

        const botMessage = {
          id: Date.now(),
          text: resultText,
          sender: 'bot',
          timestamp: new Date(),
          options: ['🔙 Voltar ao Financeiro', '🏠 Menu Principal']
        };

        setMessages(prev => [...prev, botMessage]);
        setShowDebtForm(false);
        setCustomerInfo(prev => ({ ...prev, customerId: '' }));
      }
    } catch (error) {
      console.error('Error consulting debt:', error);
      const errorMessage = {
        id: Date.now(),
        text: 'Erro ao consultar débitos. Tente novamente.',
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBoletoGeneration = async () => {
    if (!customerInfo.customerId.trim() || !customerInfo.value || !customerInfo.dueDate) {
      alert('Por favor, preencha todos os campos obrigatórios');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/generate-boleto`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_id: customerInfo.customerId,
          value: parseFloat(customerInfo.value),
          due_date: customerInfo.dueDate,
          description: customerInfo.description || 'Cobrança Linktrac',
          session_id: sessionId
        }),
      });

      if (response.ok) {
        const data = await response.json();
        let resultText = '📋 **Boleto Gerado com Sucesso!**\n\n';
        
        if (data.data.error) {
          resultText = `❌ Erro: ${data.data.error}`;
        } else {
          resultText += `✅ **ID do Pagamento:** ${data.data.id}\n`;
          resultText += `💰 **Valor:** R$ ${data.data.value}\n`;
          resultText += `📅 **Vencimento:** ${data.data.dueDate}\n`;
          if (data.data.invoiceUrl) {
            resultText += `🔗 **Link do Boleto:** ${data.data.invoiceUrl}\n`;
          }
          if (data.data.bankSlipUrl) {
            resultText += `📄 **Código de Barras:** ${data.data.bankSlipUrl}`;
          }
        }

        const botMessage = {
          id: Date.now(),
          text: resultText,
          sender: 'bot',
          timestamp: new Date(),
          options: ['🔙 Voltar ao Financeiro', '🏠 Menu Principal']
        };

        setMessages(prev => [...prev, botMessage]);
        setShowBoletoForm(false);
        setCustomerInfo({
          customerId: '',
          value: '',
          dueDate: '',
          description: ''
        });
      }
    } catch (error) {
      console.error('Error generating boleto:', error);
      const errorMessage = {
        id: Date.now(),
        text: 'Erro ao gerar boleto. Tente novamente.',
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOptionClick = (option) => {
    sendMessage(option);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>');
  };

  const renderContactInfo = (contactInfo) => {
    if (!contactInfo) return null;

    if (Array.isArray(contactInfo)) {
      // Vendedores
      return (
        <div className="contact-info">
          <h4>📞 Contatos de Vendas:</h4>
          {contactInfo.map((contact, index) => (
            <div key={index} className="contact-item">
              <strong>{contact.name}:</strong> {contact.phone}
            </div>
          ))}
        </div>
      );
    } else if (typeof contactInfo === 'object') {
      // Suporte
      return (
        <div className="contact-info">
          <h4>📞 Contatos de Suporte:</h4>
          <div className="contact-item">
            <strong>Dia:</strong> {contactInfo.dia}
          </div>
          <div className="contact-item">
            <strong>Noite:</strong> {contactInfo.noite.name} - {contactInfo.noite.phone}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <div className="header-content">
            <div className="logo-container">
              <img 
                src="https://images.unsplash.com/photo-1679403766665-67ed6cd2df30?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwxfHxjaGF0Ym90JTIwbG9nb3xlbnwwfHx8fDE3NTIxMTUyNjF8MA&ixlib=rb-4.1.0&q=85" 
                alt="Linktrac Chatbot Logo" 
                className="logo"
              />
              <div className="header-text">
                <h1>Linktrac Chatbot Suporte</h1>
                <p>Seu assistente virtual para suporte, vendas e financeiro</p>
              </div>
            </div>
          </div>
        </div>

        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.sender}`}>
              <div className="message-content">
                <div 
                  className="message-text"
                  dangerouslySetInnerHTML={{ __html: formatMessage(message.text) }}
                />
                {renderContactInfo(message.contactInfo)}
                {message.options && (
                  <div className="message-options">
                    {message.options.map((option, index) => (
                      <button
                        key={index}
                        className="option-button"
                        onClick={() => handleOptionClick(option)}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="message-timestamp">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message bot">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Debt Consultation Form */}
        {showDebtForm && (
          <div className="form-container">
            <h3>📊 Consulta de Débitos</h3>
            <input
              type="text"
              placeholder="ID do Cliente"
              value={customerInfo.customerId}
              onChange={(e) => setCustomerInfo(prev => ({ ...prev, customerId: e.target.value }))}
              className="form-input"
            />
            <button
              onClick={handleDebtConsultation}
              disabled={isLoading}
              className="form-button"
            >
              {isLoading ? 'Consultando...' : 'Consultar Débitos'}
            </button>
          </div>
        )}

        {/* Boleto Generation Form */}
        {showBoletoForm && (
          <div className="form-container">
            <h3>📋 Geração de Boleto</h3>
            <input
              type="text"
              placeholder="ID do Cliente *"
              value={customerInfo.customerId}
              onChange={(e) => setCustomerInfo(prev => ({ ...prev, customerId: e.target.value }))}
              className="form-input"
            />
            <input
              type="number"
              step="0.01"
              placeholder="Valor (R$) *"
              value={customerInfo.value}
              onChange={(e) => setCustomerInfo(prev => ({ ...prev, value: e.target.value }))}
              className="form-input"
            />
            <input
              type="date"
              placeholder="Data de Vencimento *"
              value={customerInfo.dueDate}
              onChange={(e) => setCustomerInfo(prev => ({ ...prev, dueDate: e.target.value }))}
              className="form-input"
            />
            <input
              type="text"
              placeholder="Descrição (opcional)"
              value={customerInfo.description}
              onChange={(e) => setCustomerInfo(prev => ({ ...prev, description: e.target.value }))}
              className="form-input"
            />
            <button
              onClick={handleBoletoGeneration}
              disabled={isLoading}
              className="form-button"
            >
              {isLoading ? 'Gerando...' : 'Gerar Boleto'}
            </button>
          </div>
        )}

        <div className="chat-input">
          <div className="input-container">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite sua mensagem..."
              className="message-input"
              rows="1"
            />
            <button
              onClick={() => sendMessage()}
              disabled={isLoading || !inputMessage.trim()}
              className="send-button"
            >
              📤
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;