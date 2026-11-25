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
      {favorites.map(fav => {
        const post = fav.post_detail;
        return (
          <div key={fav.id} className="post-card" onClick={() => navigate(`/post/${fav.post}`)}>
            {post?.image && (
              <img
                src={post.image.startsWith('http') ? post.image : `http://127.0.0.1:8080${post.image}`}
                alt={post.title}
                className="post-image"
              />
            )}
            <div className="post-content">
              <h2 className="post-title">{post?.title}</h2>
              <div className="post-meta">
                <span>{post?.author?.username}</span>
                <span>📅 {new Date(fav.created_at).toLocaleDateString()}</span>
              </div>
              <div className="post-excerpt">{post?.text?.substring(0, 150)}...</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
