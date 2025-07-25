import type { classes } from '../lib/db/interface'

const Classes = ({ classes }: { classes: classes[] }) => {
    return (
        <div>
            <h1>Classes</h1>
            <ul>
                {classes.map((cls) => (
                    <li key={cls.id}>
                        <h2>{cls.className}</h2>
                        <p>{cls.description}</p>
                        <p>Active from {cls.activeStart} to {cls.activeEnd}</p>
                    </li>
                ))}
            </ul>
        </div>
    )
}

export default Classes;
