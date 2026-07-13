import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

const textareaStyle = {
  width: '100%',
  padding: '1rem',
  borderRadius: '24px',
  background: 'rgba(255,255,255,0.1)',
  border: '1px solid rgba(255,255,255,0.2)',
  color: 'white',
  fontFamily: 'inherit',
  resize: 'vertical',
};

const replyTextareaStyle = {
  width: '100%',
  padding: '0.7rem 1rem',
  borderRadius: '16px',
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid rgba(255,255,255,0.15)',
  color: 'white',
  fontFamily: 'inherit',
  fontSize: '0.9rem',
  resize: 'vertical',
  marginTop: '0.5rem',
};

const actionsStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '1rem',
  marginTop: '0.5rem',
};

const iconBtnStyle = {
  background: 'none',
  border: 'none',
  color: '#94a3b8',
  cursor: 'pointer',
  fontSize: '0.85rem',
  padding: '0.2rem 0.4rem',
  borderRadius: '8px',
  transition: '0.2s',
};

function CommentItem({ comment, user, onLike, replyTo, setReplyTo, replyText, setReplyText, onReply }) {
  const isReplying = replyTo === comment.id;

  return (
    <div style={{
      background: '#1e293b',
      borderRadius: '20px',
      padding: '1rem 1.2rem',
      marginBottom: '0.8rem',
      borderLeft: '3px solid #f97316',
    }}>
      <div style={{ fontWeight: 600, color: '#f97316', marginBottom: '0.3rem', fontSize: '0.9rem' }}>
        {comment.author?.username}
      </div>
      <div style={{ color: '#cbd5e1', lineHeight: 1.5 }}>{comment.text}</div>

      <div style={actionsStyle}>
        <button
          style={{ ...iconBtnStyle, color: comment.is_liked ? '#ef4444' : '#94a3b8' }}
          onClick={() => onLike(comment.id)}
        >
          {comment.is_liked ? '❤️' : '🤍'} {comment.likes_count || 0}
        </button>
        {user && (
          <button
            style={{ ...iconBtnStyle, color: isReplying ? '#f97316' : '#94a3b8' }}
            onClick={() => setReplyTo(isReplying ? null : comment.id)}
          >
            {isReplying ? '✖ Отмена' : '💬 Ответить'}
          </button>
        )}
      </div>

      {isReplying && (
        <form onSubmit={(e) => onReply(e, comment.id)} style={{ marginTop: '0.5rem' }}>
          <textarea
            rows={2}
            placeholder={`Ответ ${comment.author?.username}...`}
            value={replyText}
            onChange={e => setReplyText(e.target.value)}
            style={replyTextareaStyle}
          />
          <button type="submit" style={{
            marginTop: '0.4rem',
            padding: '0.35rem 1.2rem',
            background: 'linear-gradient(135deg, #f97316, #ec4899)',
            border: 'none',
            borderRadius: '20px',
            color: 'white',
            fontWeight: 600,
            fontSize: '0.85rem',
            cursor: 'pointer',
          }}>
            Отправить ответ
          </button>
        </form>
      )}

      {comment.replies?.map(reply => (
        <div key={reply.id} style={{
          marginLeft: '1.5rem',
          marginTop: '0.8rem',
          paddingLeft: '1rem',
          borderLeft: '2px solid #4c1d95',
        }}>
          <div style={{ fontWeight: 600, color: '#a78bfa', marginBottom: '0.2rem', fontSize: '0.85rem' }}>
            {reply.author?.username}
          </div>
          <div style={{ color: '#cbd5e1', lineHeight: 1.5 }}>{reply.text}</div>
          <div style={{ marginTop: '0.3rem' }}>
            <button
              style={{ ...iconBtnStyle, color: reply.is_liked ? '#ef4444' : '#94a3b8', fontSize: '0.8rem' }}
              onClick={() => onLike(reply.id)}
            >
              {reply.is_liked ? '❤️' : '🤍'} {reply.likes_count || 0}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function PostDetail() {
  const { id } = useParams();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentText, setCommentText] = useState('');
  const [replyTo, setReplyTo] = useState(null);
  const [replyText, setReplyText] = useState('');
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

  const handleReply = async (e, commentId) => {
    e.preventDefault();
    if (!replyText.trim()) return;
    try {
      await api.post(`/posts/${id}/comments/`, { text: replyText, parent: commentId });
      setReplyText('');
      setReplyTo(null);
      fetchComments();
    } catch (err) {
      console.error('Reply error:', err.response?.data || err.message);
      alert(err.response?.data?.detail || err.response?.data?.parent?.[0] || 'Ошибка отправки ответа');
    }
  };

  const handleLikeComment = async (commentId) => {
    if (!user) return;
    await api.post(`/posts/${id}/comments/${commentId}/like/`);
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
        {post.image && (
          <img
            src={post.image.startsWith('http') ? post.image : `http://127.0.0.1:8080${post.image}`}
            alt={post.title}
            className="post-image"
          />
        )}
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
            rows={3}
            placeholder="Написать комментарий..."
            value={commentText}
            onChange={e => setCommentText(e.target.value)}
            style={textareaStyle}
          />
          <button type="submit" className="read-more" style={{ marginTop: '0.5rem' }}>
            Отправить
          </button>
        </form>
      )}
      {comments.map(comment => (
        <CommentItem
          key={comment.id}
          comment={comment}
          user={user}
          onLike={handleLikeComment}
          replyTo={replyTo}
          setReplyTo={setReplyTo}
          replyText={replyText}
          setReplyText={setReplyText}
          onReply={handleReply}
        />
      ))}
    </div>
  );
}
