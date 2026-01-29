import { cn } from '../lib/utils';
import { Keyboard } from 'lucide-react';

interface DictationInputProps {
    value: string;
    onChange: (val: string) => void;
    placeholder?: string;
    className?: string;
}

export default function DictationInput({ value, onChange, placeholder = "Type what you hear...", className }: DictationInputProps) {
    return (
        <div className={cn("space-y-2", className)}>
            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <Keyboard size={16} /> Dictation
            </label>
            <textarea
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                className="w-full min-h-[100px] p-4 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all font-mono text-sm leading-relaxed resize-y"
            />
        </div>
    )
}
