import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ExternalLink } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  isAssistant?: boolean;
}

export default function MarkdownRenderer({ content, className = '', isAssistant = false }: MarkdownRendererProps) {
  return (
    <div className={`prose prose-sm max-w-none 
      ${isAssistant ? 'prose-slate dark:prose-invert' : 'prose-indigo'}
      prose-headings:font-bold prose-headings:text-slate-900 dark:prose-headings:text-white
      prose-p:leading-relaxed prose-p:text-slate-700 dark:prose-p:text-slate-300
      prose-strong:text-slate-900 dark:prose-strong:text-white prose-strong:font-semibold
      prose-li:text-slate-700 dark:prose-li:text-slate-300
      prose-a:text-blue-500 prose-a:no-underline hover:prose-a:underline
      prose-code:px-1.5 prose-code:py-0.5 prose-code:bg-slate-100 dark:prose-code:bg-slate-800 prose-code:rounded-md prose-code:text-indigo-600 dark:prose-code:text-indigo-400 prose-code:before:content-none prose-code:after:content-none
      prose-pre:bg-slate-900 prose-pre:text-slate-100 prose-pre:rounded-xl
      ${className}`}>
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ node, ...props }) => (
            <a 
              {...props} 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 font-bold text-blue-500 hover:text-blue-600 transition-colors group"
            >
              {props.children}
              <ExternalLink size={12} className="opacity-50 group-hover:opacity-100 transition-opacity" />
            </a>
          ),
          // Example of custom styling for bold text with a subtle highlight
          strong: ({ node, ...props }) => (
            <strong {...props} className="font-bold text-slate-900 dark:text-white bg-slate-100/50 dark:bg-slate-800/50 px-1 rounded" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
