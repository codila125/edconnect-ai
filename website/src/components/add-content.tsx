export default function addContent() {
    return (
        <div>
            <h1>Add Content</h1>
            <form method="post" action="/api/addcontent">
                <label>
                    Class ID:
                    <input type="text" name="classId" required />
                </label>
                <br />
                <label>
                    Title:
                    <input type="text" name="title" required />
                </label>
                <br />
                <label>
                    Body:
                    <textarea name="body" required></textarea>
                </label>
                <br />
                <label>
                    URL:
                    <input type="url" name="url" />
                </label>
                <label>
                    Type:
                    <select name="type" required>
                        <option value="material">Material</option>
                        <option value="assignment">Assignment</option>
                    </select>
                </label>
                <br />
                <label>
                    Deadline (optional, for assignments only):
                    <input type="date" name="deadline" />
                </label>
                <br />
                <button type="submit">Add Content</button>
            </form>
        </div>
    );
}
