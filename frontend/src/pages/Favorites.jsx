import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

export default function Favorites() {
  const [favorites, setFavorites] = useState([]);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      api.get('/favorites/').then(res => {
        setFavorites(res.data.results || res.data);
      });
    }
  }, [user]);

  if (!user) return <div className="container">Требуется вход</div>;

  return (
    <div className="container">
      <h1 style={{ fontSize: '2rem', marginBottom: '1.5rem' }}>❤️ Избранное</h1>
      {favorites.length === 0 && <p>Нет избранных постов</p>}
      {favorites.map(fav => (
        <div key={fav.id} className="post-card" onClick={() => navigate(`/post/${fav.post.id}`)}>
          <h2 className="post-title">{fav.post.title}</h2>
          <div className="post-meta">📅 {new Date(fav.created_at).toLocaleDateString()}</div>
          <div className="post-excerpt">{fav.post.text?.substring(0, 150)}...</div>
          <button className="read-more">Читать →</button>
        </div>
      ))}
    </div>
  );
}