import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(username, password);
      navigate('/');
    } catch {
      setError('Неверный логин или пароль');
    }
  };

  return (
    <div className="container">
      <div className="auth-form">
        <h2>Вход</h2>
        {error && <p style={{ color: '#ffa5a5', textAlign: 'center' }}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <input type="text" placeholder="Логин" value={username} onChange={e => setUsername(e.target.value)} required />
          <input type="password" placeholder="Пароль" value={password} onChange={e => setPassword(e.target.value)} required />
          <button type="submit">Войти</button>
        </form>
        <div className="link">Нет аккаунта? <Link to="/register">Зарегистрироваться</Link></div>
      </div>
    </div>
  );
}