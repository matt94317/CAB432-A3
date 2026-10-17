export default function FullPageSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center" role="status">
      <div className="size-8 animate-spin rounded-full border-4 border-gray-200 border-t-brand" />
      <span className="sr-only">Loading</span>
    </div>
  );
}
