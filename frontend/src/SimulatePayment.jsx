import React, { useState } from 'react';

function SimulatePayment({ onSubmit }) {
  const [formData, setFormData] = useState({
    customer_id: '',
    amount: '',
    payment_reference: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!formData.customer_id || !formData.amount || !formData.payment_reference) {
      alert('Please fill in all fields');
      return;
    }

    const paymentData = {
      ...formData,
      amount: parseFloat(formData.amount),
      currency: 'USD',
      merchant_id: 'merchant_demo',
      idempotency_key: `idem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };

    onSubmit(paymentData);

    // Reset form
    setFormData({
      customer_id: '',
      amount: '',
      payment_reference: ''
    });
  };

  return (
    <div className="simulate-payment">
      <h2>Simulate Payment Notification</h2>
      <form onSubmit={handleSubmit} className="payment-form">
        <div className="form-group">
          <label htmlFor="customer_id">Customer ID:</label>
          <input
            type="text"
            id="customer_id"
            name="customer_id"
            value={formData.customer_id}
            onChange={handleInputChange}
            placeholder="e.g., cust_12345"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="amount">Amount:</label>
          <input
            type="number"
            id="amount"
            name="amount"
            value={formData.amount}
            onChange={handleInputChange}
            placeholder="e.g., 99.99"
            min="0.01"
            step="0.01"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="payment_reference">Payment Reference:</label>
          <input
            type="text"
            id="payment_reference"
            name="payment_reference"
            value={formData.payment_reference}
            onChange={handleInputChange}
            placeholder="e.g., PAY_2024_001"
            required
          />
        </div>

        <button type="submit" className="submit-btn">
          Generate Token
        </button>
      </form>
    </div>
  );
}

export default SimulatePayment;