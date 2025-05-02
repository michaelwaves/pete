"use client"
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Book, CheckCircle, ChevronLeft, ChevronRight, Circle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';

// Types based on your Zod schema
type Answer = {
  answer: string;
  is_correct: boolean;
};

type Question = {
  question: string;
  answers: Answer[];
};

type Unit = {
  markdown: string;
  quiz: Question[];
};

type CourseData = {
  units: Unit[];
  language: string;
};

// Example data based on your schema
const exampleCourseData: CourseData = {
  language: "English",
  units: [
    {
      markdown: "# Introduction to React\n\nReact is a JavaScript library for building user interfaces. It allows you to create reusable UI components and efficiently update your interface when your data changes.\n\n## Key Concepts\n\n- **Components**: The building blocks of React applications\n- **Props**: How data is passed between components\n- **State**: How components remember things\n\n```jsx\nfunction HelloWorld() {\n  return <h1>Hello, world!</h1>;\n}\n```",
      quiz: [
        {
          question: "What is React primarily used for?",
          answers: [
            { answer: "Building user interfaces", is_correct: true },
            { answer: "Server-side programming", is_correct: false },
            { answer: "Database management", is_correct: false },
            { answer: "Network security", is_correct: false }
          ]
        },
        {
          question: "Which of the following is NOT a key concept in React?",
          answers: [
            { answer: "Components", is_correct: false },
            { answer: "Props", is_correct: false },
            { answer: "State", is_correct: false },
            { answer: "SQL Queries", is_correct: true }
          ]
        }
      ]
    },
    {
      markdown: "# Components in React\n\nComponents are the core building blocks of a React application. A component is a self-contained module that renders some output.\n\n## Types of Components\n\n1. **Functional Components** - Simple components using functions\n2. **Class Components** - More feature-rich components using ES6 classes\n\n## Example Functional Component\n\n```jsx\nfunction Greeting({ name }) {\n  return <h1>Hello, {name}!</h1>;\n}\n```",
      quiz: [
        {
          question: "What are the two main types of components in React?",
          answers: [
            { answer: "Functional and Class components", is_correct: true },
            { answer: "HTML and CSS components", is_correct: false },
            { answer: "Static and Dynamic components", is_correct: false },
            { answer: "Frontend and Backend components", is_correct: false }
          ]
        },
        {
          question: "Which syntax is typically used for functional components?",
          answers: [
            { answer: "ES6 class syntax", is_correct: false },
            { answer: "Function syntax", is_correct: true },
            { answer: "Python decorator syntax", is_correct: false },
            { answer: "Java annotation syntax", is_correct: false }
          ]
        }
      ]
    }
  ]
};

export default function CourseInterface() {
  const [courseData, setCourseData] = useState<CourseData>(exampleCourseData);
  const [currentUnitIndex, setCurrentUnitIndex] = useState(0);
  const [showingQuiz, setShowingQuiz] = useState(false);
  const [userAnswers, setUserAnswers] = useState<(number | null)[]>([]);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const currentUnit = courseData.units[currentUnitIndex];
  const totalUnits = courseData.units.length;
  const progress = ((currentUnitIndex + 1) / totalUnits) * 100;

  const handleAnswerSelect = (questionIndex: number, answerIndex: number) => {
    const newUserAnswers = [...userAnswers];
    newUserAnswers[questionIndex] = answerIndex;
    setUserAnswers(newUserAnswers);
  };

  const handleSubmitQuiz = () => {
    setHasSubmitted(true);
  };

  const handleNextUnit = () => {
    if (currentUnitIndex < totalUnits - 1) {
      setCurrentUnitIndex(currentUnitIndex + 1);
      setShowingQuiz(false);
      setUserAnswers([]);
      setHasSubmitted(false);
    }
  };

  const handlePrevUnit = () => {
    if (currentUnitIndex > 0) {
      setCurrentUnitIndex(currentUnitIndex - 1);
      setShowingQuiz(false);
      setUserAnswers([]);
      setHasSubmitted(false);
    }
  };

  const calculateScore = () => {
    let correct = 0;
    currentUnit.quiz.forEach((question, index) => {
      const userAnswerIndex = userAnswers[index];
      if (userAnswerIndex !== null && question.answers[userAnswerIndex].is_correct) {
        correct++;
      }
    });
    return `${correct}/${currentUnit.quiz.length}`;
  };

  const allQuestionsAnswered = () => {
    return userAnswers.length === currentUnit.quiz.length &&
      userAnswers.every(answer => answer !== null && answer !== undefined);
  };

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <header className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold flex items-center">
            <Book className="mr-2" /> Course Content
          </h1>
          <div className="text-sm text-gray-500">
            Language: {courseData.language}
          </div>
        </div>
        <div className="mb-2">
          <Progress value={progress} className="h-2" />
        </div>
        <div className="flex justify-between text-sm">
          <span>Unit {currentUnitIndex + 1} of {totalUnits}</span>
          <span>{Math.round(progress)}% complete</span>
        </div>
      </header>

      <Tabs value={showingQuiz ? "quiz" : "content"}
        onValueChange={(value) => setShowingQuiz(value === "quiz")}>
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="content">Learning Material</TabsTrigger>
          <TabsTrigger value="quiz">Quiz</TabsTrigger>
        </TabsList>

        <TabsContent value="content">
          <Card>
            <CardHeader>
              <CardTitle>Unit {currentUnitIndex + 1}</CardTitle>
              <CardDescription>Study the material below</CardDescription>
            </CardHeader>
            <CardContent className="prose max-w-none">
              <ReactMarkdown>
                {currentUnit.markdown}
              </ReactMarkdown>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button
                variant="outline"
                onClick={handlePrevUnit}
                disabled={currentUnitIndex === 0}
              >
                <ChevronLeft className="mr-2 h-4 w-4" /> Previous
              </Button>
              <Button onClick={() => setShowingQuiz(true)}>
                Take Quiz
              </Button>
              <Button
                onClick={handleNextUnit}
                disabled={currentUnitIndex === totalUnits - 1}
              >
                Next <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>

        <TabsContent value="quiz">
          <Card>
            <CardHeader>
              <CardTitle>Unit {currentUnitIndex + 1} Quiz</CardTitle>
              <CardDescription>
                Test your knowledge with these multiple-choice questions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {currentUnit.quiz.map((question, qIndex) => (
                <div key={qIndex} className="mb-8">
                  <h3 className="text-lg font-medium mb-4">{qIndex + 1}. {question.question}</h3>
                  <div className="space-y-3">
                    {question.answers.map((answer, aIndex) => {
                      const isSelected = userAnswers[qIndex] === aIndex;
                      const showCorrect = hasSubmitted && answer.is_correct;
                      const showIncorrect = hasSubmitted && isSelected && !answer.is_correct;

                      return (
                        <div
                          key={aIndex}
                          className={`p-3 rounded-lg border transition-colors flex items-center
                            ${isSelected ? 'bg-blue-50 border-blue-300' : 'hover:bg-gray-50'} 
                            ${showCorrect ? 'bg-green-50 border-green-300' : ''} 
                            ${showIncorrect ? 'bg-red-50 border-red-300' : ''}`}
                          onClick={() => !hasSubmitted && handleAnswerSelect(qIndex, aIndex)}
                        >
                          <div className="mr-3">
                            {hasSubmitted ? (
                              answer.is_correct ? (
                                <CheckCircle className="text-green-500 h-5 w-5" />
                              ) : isSelected ? (
                                <XCircle className="text-red-500 h-5 w-5" />
                              ) : (
                                <Circle className="text-gray-300 h-5 w-5" />
                              )
                            ) : (
                              isSelected ? (
                                <CheckCircle className="text-blue-500 h-5 w-5" />
                              ) : (
                                <Circle className="text-gray-300 h-5 w-5" />
                              )
                            )}
                          </div>
                          <div className="flex-1">{answer.answer}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}

              {hasSubmitted && (
                <Alert className="mt-6">
                  <AlertDescription>
                    Your Score: {calculateScore()}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button
                variant="outline"
                onClick={() => setShowingQuiz(false)}
              >
                Back to Content
              </Button>

              {!hasSubmitted ? (
                <Button
                  onClick={handleSubmitQuiz}
                  disabled={!allQuestionsAnswered()}
                >
                  Submit Answers
                </Button>
              ) : (
                <Button
                  onClick={handleNextUnit}
                  disabled={currentUnitIndex === totalUnits - 1}
                >
                  Next Unit <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              )}
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}