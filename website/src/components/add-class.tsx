export default function addClass() {
    return (
        <div>
            <h1>Add Class</h1>
            <form method="post" action="/api/addclasses">
                <label>
                    Class Name:
                    <input type="text" name="name" required />
                </label>
                <br />
                <label>
                    Description:
                    <textarea name="description" required></textarea>
                </label>
                <label>
                    Active Hours:
                    <input type="time" name="activestart" required />
                    to
                    <input type="time" name="activeend" required />
                </label>
                <br />
                <button type="submit">Add Class</button>
            </form>
        </div>
    );
}
