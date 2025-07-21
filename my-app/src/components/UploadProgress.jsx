export default function UploadProgress({ progress }) {
  if (progress === 0) return null;

  return (
    <div className="w-full mt-4">
      <label className="block mb-1 text-sm text-gray-700">Uploading...</label>
      <div className="w-full bg-gray-200 rounded-full h-4">
        <div
          className="bg-green-500 h-4 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
    </div>
  );
}