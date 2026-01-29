import { useMemo } from 'react';
import { diffWords } from 'diff';
import { cn } from '../lib/utils';

interface DiffViewerProps {
    userText: string;
    correctText: string;
    className?: string;
}

export default function DiffViewer({ userText, correctText, className }: DiffViewerProps) {
    const diff = useMemo(() => {
        if (!userText && !correctText) return [];
        return diffWords(userText || "", correctText || "");
    }, [userText, correctText]);

    if (!userText) {
        return (
             <div className="text-red-500 italic">No transcript provided.</div>
        )
    }

    return (
        <div className={cn("font-mono text-sm leading-7 p-4 bg-gray-50 rounded-lg border border-gray-200", className)}>
            {diff.map((part, index) => {
                if (part.added) {
                    return (
                        <span key={index} className="bg-green-100 text-green-800 px-1 rounded mx-0.5 border border-green-200" title="Missing word">
                            {part.value}
                        </span>
                    );
                }
                if (part.removed) {
                    return (
                        <span key={index} className="bg-red-100 text-red-800 decoration-red-400 line-through px-1 rounded mx-0.5 border border-red-200" title="Incorrect word">
                            {part.value}
                        </span>
                    );
                }
                return <span key={index}>{part.value}</span>;
            })}
        </div>
    );
}

