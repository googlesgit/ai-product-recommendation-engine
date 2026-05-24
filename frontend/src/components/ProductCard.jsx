export default function ProductCard({
  product,
  onSelect,
  onLike,
  selected,
  showScore,
  showRelevance,
  compact,
}) {
  return (
    <article
      className={`card ${selected ? 'selected' : ''} ${compact ? 'card-compact' : ''}`}
      onClick={() => onSelect?.(product)}
    >
      <div className="category">{product.category}</div>
      <h3>{product.name}</h3>
      <p className="desc">{product.description}</p>
      <div className="meta">
        <span>${Number(product.price).toFixed(2)}</span>
        <span>★ {product.rating} ({product.review_count} reviews)</span>
      </div>
      {showScore && product.similarity_score != null && (
        <p className="score">Similarity: {(product.similarity_score * 100).toFixed(1)}%</p>
      )}
      {showRelevance && product.relevance_score != null && (
        <p className="score relevance">Match score: {product.relevance_score}</p>
      )}
      {product.recommendation_reason && (
        <p className="reason">{product.recommendation_reason}</p>
      )}
      {onLike && (
        <button
          type="button"
          className="btn btn-outline"
          onClick={(e) => {
            e.stopPropagation();
            onLike(product);
          }}
        >
          ♥ Like
        </button>
      )}
    </article>
  );
}
