import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { FaSearch, FaHeart, FaEnvelope, FaUser, FaCog, FaSignOutAlt, FaPenAlt } from 'react-icons/fa';
import Avatar from 'react-avatar';

export default function Navbar() {
  const { user, logout, unreadCount } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef();

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setShowMenu(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) navigate(`/?search=${encodeURIComponent(searchQuery)}`);
    setSearchQuery('');
  };

  const handleLogout = () => {
    logout();
    navigate('/');
    setShowMenu(false);
  };

  return (
    <nav className="navbar">
      <Link to="/" className="logo">
        ✨ Делимся мыслями
      </Link>
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          placeholder="Поиск..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button type="submit"><FaSearch /></button>
      </form>
      <div className="navbar-right">
        {user ? (
          <>
            <Link to="/create-post" className="icon-link" title="Написать пост">
              <FaPenAlt />
            </Link>
            <Link to="/favorites" className="icon-link"><FaHeart /></Link>
            <Link to="/messages" className="icon-link">
              <FaEnvelope />
              {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
            </Link>
            <div className="user-menu" ref={menuRef}>
              <button className="avatar-btn" onClick={() => setShowMenu(!showMenu)}>
                <Avatar name={user.username} size="36" round="40px" />
              </button>
              {showMenu && (
                <div className="dropdown-menu">
                  <Link to="/profile" onClick={() => setShowMenu(false)}><FaUser /> Профиль</Link>
                  <Link to="/profile/settings" onClick={() => setShowMenu(false)}><FaCog /> Настройки</Link>
                  <button onClick={handleLogout}><FaSignOutAlt /> Выйти</button>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="auth-buttons">
            <Link to="/login">Вход</Link>
            <Link to="/register" className="register-btn">Регистрация</Link>
          </div>
        )}
      </div>
    </nav>
  );
}