export default function JoinClass() {
    return (
        <div>
            <h1>Join Class</h1>
            <form method="post" action="/api/joinclass">
                <label>
                    Class Code:
                    <input type="text" name="code" required />
                </label>
                <button type="submit">Join Class</button>
            </form>
        </div>
    );
}
