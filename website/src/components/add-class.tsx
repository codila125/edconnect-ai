export default function addClass() {
    return (
        <div>
            <h1>Add Class</h1>
            <form method="post" action="/api/classes">
                <label>
                    Class Name:
                    <input type="text" name="name" required />
                </label>
                <br />
                <label>
                    Description:
                    <textarea name="description" required></textarea>
                </label>
                <br />
                <button type="submit">Add Class</button>
            </form>
        </div>
    );
}
