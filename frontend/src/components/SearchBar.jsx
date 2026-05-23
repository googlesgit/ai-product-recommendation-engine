export default function SearchBar({ value, onChange, onSubmit }) {
  return (
    <form
      className="controls"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit?.(value);
      }}
    >
      <input
        type="search"
        className="search-input"
        placeholder="Search products (name, category, description)..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </form>
  );
}
