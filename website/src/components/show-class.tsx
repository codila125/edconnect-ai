import { useNavigate } from "@tanstack/react-router";
import type { classes } from "../lib/db/interface";

const Classes = ({ classes }: { classes: classes[] }) => {
    const navigate = useNavigate();

    return (
        <div>
            <h1>Classes</h1>
            <ul>
                {classes.map((cls) => (
                    <li key={cls.id}>
                        <button onClick={() => {
                            navigate({ to: `/contents/${cls.id}` });
                        }}>
                            <h2>{cls.className}</h2>
                            <p>{cls.description}</p>
                            <p>
                                Active from {cls.activeStart} to {cls.activeEnd}
                            </p>
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Classes;
