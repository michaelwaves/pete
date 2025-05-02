import CourseInterface from "./CourseInterface";

async function CoursePage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    return (
        <div>
            <h1>Course {id}</h1>
            <CourseInterface />
        </div>
    );
}

export default CoursePage;