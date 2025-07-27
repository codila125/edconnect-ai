export default function JoinClass() {
  return (
    <div className="max-w-md mx-auto p-4">
      <h1 className="text-lg font-medium mb-4">Join Class</h1>
      
      <form method="post" action="/api/joinclass" className="space-y-4">
        <div>
          <label className="block text-sm mb-1">
            Class Code
          </label>
          <input 
            type="text" 
            name="code" 
            required 
            className="w-full p-2 border rounded"
            placeholder="Enter class code"
          />
        </div>
        
        <button 
          type="submit"
          className="w-full p-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Join Class
        </button>
      </form>
    </div>
  );
}