import React from 'react';

function TokensTable({ tokens, onTokenSelect, selectedTokenId }) {
  const formatDate = (dateString) => {
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

  return (
    <div className="tokens-table">
      <h2>Recent Tokens</h2>
      {tokens.length === 0 ? (
        <div className="no-tokens">
          <p>No tokens found. Generate a token using the payment form above.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Token ID</th>
                <th>Status</th>
                <th>Amount</th>
                <th>Issued At</th>
              </tr>
            </thead>
            <tbody>
              {tokens.map((token) => (
                <tr
                  key={token.token_id}
                  className={selectedTokenId === token.token_id ? 'selected' : ''}
                  onClick={() => onTokenSelect(token.token_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <td className="token-id">
                    {token.token_id.substring(0, 12)}...
                  </td>
                  <td>
                    <span className={getStatusBadgeClass(token.status)}>
                      {token.status}
                    </span>
                  </td>
                  <td className="amount">
                    ${typeof token.amount === 'number' ? token.amount.toFixed(2) : token.amount}
                  </td>
                  <td className="date">
                    {formatDate(token.issued_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default TokensTable;