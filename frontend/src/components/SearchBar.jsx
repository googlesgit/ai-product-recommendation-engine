export default function SearchBar({
  value,
  onChange,
  onSubmit,
  onClear,
  searching,
  suggestions = [],
  onPickSuggestion,
}) {
  return (
    <div className="search-wrap">
      <form
        className="search-form"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit?.(value);
        }}
      >
        <input
          type="search"
          className="search-input"
          placeholder="Search products — try headphones, microwave, yoga, books..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-label="Search products"
        />
        <button type="submit" className="btn" disabled={searching}>
          {searching ? 'Searching…' : 'Search'}
        </button>
        {value && (
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => onClear?.()}
            aria-label="Clear search"
          >
            Clear
          </button>
        )}
      </form>
      {suggestions.length > 0 && value.trim() && (
        <ul className="search-suggestions" role="listbox">
          {suggestions.map((s) => (
            <li key={s}>
              <button type="button" onClick={() => onPickSuggestion?.(s)}>
                {s}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
