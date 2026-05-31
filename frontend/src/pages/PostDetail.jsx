import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

export default function PostDetail() {
  const { id } = useParams();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentText, setCommentText] = useState('');
  const { user } = useAuth();

  const fetchPost = async () => {
    const res = await api.get(`/posts/${id}/`);
    setPost(res.data);
  };
  const fetchComments = async () => {
    const res = await api.get(`/posts/${id}/comments/`);
    setComments(res.data.results || res.data);
  };

  useEffect(() => {
    fetchPost();
    fetchComments();
  }, [id]);

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    await api.post(`/posts/${id}/comments/`, { text: commentText });
    setCommentText('');
    fetchComments();
  };

  const handleFavorite = async () => {
    if (!user) return;
    if (post?.is_favorited) {
      const favs = await api.get('/favorites/');
      const favItem = (favs.data.results || favs.data).find(f => f.post === post.id);
      if (favItem) await api.delete(`/favorites/${favItem.id}/`);
    } else {
      await api.post('/favorites/', { post: post.id });
    }
    fetchPost();
  };

  if (!post) return <div className="container">Загрузка...</div>;

  return (
    <div className="container">
      <div className="post-detail">
        {post.image && <img src={post.image} alt={post.title} className="post-image" />}
        <h1>{post.title}</h1>
        <div className="post-meta">
          <span>{post.author?.username}</span>
          <span>{new Date(post.created_at).toLocaleDateString()}</span>
          <span>👁️ {post.views}</span>
          <button onClick={handleFavorite} className="fav-btn">
            {post.is_favorited ? '❤️ В избранном' : '🤍 В избранное'}
          </button>
        </div>
        <div className="content">{post.text}</div>
      </div>

      <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>💬 Комментарии</h3>
      {user && (
        <form onSubmit={handleAddComment} style={{ marginBottom: '2rem' }}>
          <textarea
            rows="3"
            placeholder="Написать комментарий..."
            value={commentText}
            onChange={e => setCommentText(e.target.value)}
            style={{
              width: '100%',
              padding: '1rem',
              borderRadius: '24px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              color: 'white',
              fontFamily: 'inherit'
            }}
          />
          <button type="submit" className="read-more" style={{ marginTop: '0.5rem' }}>Отправить</button>
        </form>
      )}
      {comments.map(comment => (
        <div key={comment.id} className="comment">
          <div className="comment-author">{comment.author?.username}</div>
          <div className="comment-text">{comment.text}</div>
          {comment.replies?.map(reply => (
            <div key={reply.id} className="comment" style={{ marginLeft: '2rem', marginTop: '0.5rem' }}>
              <div className="comment-author">{reply.author?.username}</div>
              <div className="comment-text">{reply.text}</div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}