import React from 'react';

function TokenDetail({ token }) {
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'active':
        return 'status-badge status-active';
      case 'frozen':
        return 'status-badge status-frozen';
      case 'revoked':
        return 'status-badge status-revoked';
      default:
        return 'status-badge status-unknown';
    }
  };

  if (!token) {
    return (
      <div className="token-detail">
        <h2>Token Details</h2>
        <div className="no-selection">
          <p>Select a token from the table to view its details.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="token-detail">
      <h2>Token Details</h2>
      <div className="detail-content">
        <div className="detail-row">
          <label>Token ID:</label>
          <span className="token-id-full">{token.token_id}</span>
        </div>

        <div className="detail-row">
          <label>Status:</label>
          <span className={getStatusBadgeClass(token.status)}>
            {token.status}
          </span>
        </div>

        <div className="detail-row">
          <label>Customer ID:</label>
          <span>{token.customer_id}</span>
        </div>

        <div className="detail-row">
          <label>Merchant ID:</label>
          <span>{token.merchant_id}</span>
        </div>

        <div className="detail-row">
          <label>Payment Reference:</label>
          <span>{token.payment_reference}</span>
        </div>

        <div className="detail-row">
          <label>Amount:</label>
          <span className="amount">{token.currency} ${typeof token.amount === 'number' ? token.amount.toFixed(2) : token.amount}</span>
        </div>

        <div className="detail-row">
          <label>Currency:</label>
          <span>{token.currency}</span>
        </div>

        <div className="detail-row">
          <label>Idempotency Key:</label>
          <span className="idempotency-key">{token.idempotency_key}</span>
        </div>

        <div className="detail-row">
          <label>Issued At:</label>
          <span>{formatDate(token.issued_at)}</span>
        </div>

        <div className="detail-row">
          <label>Expires At:</label>
          <span>{formatDate(token.expires_at)}</span>
        </div>

        {token._id && (
          <div className="detail-row">
            <label>Database ID:</label>
            <span className="db-id">{token._id}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default TokenDetail;