export default function ResultsSummary({ results }) {
  const total = results.length;
  const shortlisted = results.filter(r => r.shortlisted).length;
  const rejected = total - shortlisted;

  return (
    <div className="grid grid-cols-3 gap-4 mt-6 text-center">
      <div className="bg-gray-100 p-4 rounded shadow">
        <p className="text-xl font-bold">{total.toLocaleString()}</p>
        <p className="text-sm text-gray-600">Resumes Scanned</p>
      </div>
      <div className="bg-green-100 p-4 rounded shadow">
        <p className="text-xl font-bold">{shortlisted.toLocaleString()}</p>
        <p className="text-sm text-green-700">Shortlisted</p>
      </div>
      <div className="bg-red-100 p-4 rounded shadow">
        <p className="text-xl font-bold">{rejected}</p>
        <p className="text-sm text-red-700">Rejected</p>
      </div>
    </div>
  );
}
