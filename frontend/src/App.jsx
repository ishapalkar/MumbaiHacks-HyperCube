import React, { useState, useEffect } from 'react';
import socketService from './socket';
import SimulatePayment from './SimulatePayment';
import TokensTable from './TokensTable';
import TokenDetail from './TokenDetail';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';
const MERCHANT_AUTH_KEY = 'demo_key_123';

function App() {
  const [tokens, setTokens] = useState([]);
  const [selectedToken, setSelectedToken] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');

  useEffect(() => {
    // Connect to Socket.IO
    const socket = socketService.connect();
    
    socket.on('connect', () => {
      setConnectionStatus('Connected');
    });

    socket.on('disconnect', () => {
      setConnectionStatus('Disconnected');
    });

    // Listen for token events
    socket.on('token.assigned', (data) => {
      console.log('Token assigned:', data);
      setTokens(prevTokens => [data, ...prevTokens]);
    });

    socket.on('token.frozen', (data) => {
      console.log('Token frozen:', data);
      setTokens(prevTokens => 
        prevTokens.map(token => 
          token.token_id === data.token_id 
            ? { ...token, status: 'frozen' }
            : token
        )
      );
    });

    socket.on('token.revoked', (data) => {
      console.log('Token revoked:', data);
      setTokens(prevTokens => 
        prevTokens.map(token => 
          token.token_id === data.token_id 
            ? { ...token, status: 'revoked' }
            : token
        )
      );
    });

    // Load existing tokens
    loadTokens();

    // Cleanup on unmount
    return () => {
      socketService.disconnect();
    };
  }, []);

  const loadTokens = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/tokens?merchant_id=merchant_demo`, {
        headers: {
          'Authorization': `Bearer ${MERCHANT_AUTH_KEY}`
        }
      });
      setTokens(response.data.tokens || []);
    } catch (error) {
      console.error('Error loading tokens:', error);
    }
  };

  const handleTokenSelect = async (tokenId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/token/${tokenId}`, {
        headers: {
          'Authorization': `Bearer ${MERCHANT_AUTH_KEY}`
        }
      });
      setSelectedToken(response.data.token);
    } catch (error) {
      console.error('Error loading token details:', error);
    }
  };

  const handlePaymentSubmit = async (paymentData) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/assign-token`, paymentData, {
        headers: {
          'Authorization': `Bearer ${MERCHANT_AUTH_KEY}`,
          'Content-Type': 'application/json'
        }
      });
      console.log('Payment processed:', response.data);
    } catch (error) {
      console.error('Error processing payment:', error);
      alert('Error processing payment: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Merchant Token Dashboard</h1>
        <div className="connection-status">
          <span className={`status-indicator ${connectionStatus.toLowerCase()}`}></span>
          {connectionStatus}
        </div>
      </header>

      <div className="main-content">
        <div className="left-panel">
          <SimulatePayment onSubmit={handlePaymentSubmit} />
          <TokensTable 
            tokens={tokens} 
            onTokenSelect={handleTokenSelect}
            selectedTokenId={selectedToken?.token_id}
          />
        </div>

        <div className="right-panel">
          <TokenDetail token={selectedToken} />
        </div>
      </div>
    </div>
  );
}

export default App;