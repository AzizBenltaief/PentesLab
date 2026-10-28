import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * Shared markdown renderer for AI-generated content.
 * Supports GFM (tables, strikethrough, task lists) with Tailwind styling.
 */
const Markdown = ({ children }) => (
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      h1: (props) => (
        <h1 className="text-xl font-bold text-gray-900 mt-4 mb-3 pb-2 border-b-2 border-indigo-500" {...props} />
      ),
      h2: (props) => (
        <h2 className="text-lg font-semibold text-gray-900 mt-5 mb-2" {...props} />
      ),
      h3: (props) => (
        <h3 className="text-base font-semibold text-gray-800 mt-4 mb-2" {...props} />
      ),
      h4: (props) => (
        <h4 className="text-sm font-semibold text-gray-800 mt-3 mb-1" {...props} />
      ),
      p: (props) => <p className="text-sm text-gray-700 leading-relaxed my-2" {...props} />,
      ul: (props) => <ul className="list-disc ml-5 my-2 space-y-1" {...props} />,
      ol: (props) => <ol className="list-decimal ml-5 my-2 space-y-1" {...props} />,
      li: (props) => <li className="text-sm text-gray-700 leading-relaxed" {...props} />,
      strong: (props) => <strong className="font-semibold text-gray-900" {...props} />,
      em: (props) => <em className="italic text-gray-600" {...props} />,
      a: (props) => (
        <a
          className="text-indigo-600 hover:text-indigo-800 underline"
          target="_blank"
          rel="noopener noreferrer"
          {...props}
        />
      ),
      blockquote: (props) => (
        <blockquote className="border-l-4 border-indigo-300 bg-indigo-50 pl-3 pr-2 py-1 my-3 text-sm text-gray-700" {...props} />
      ),
      hr: () => <hr className="my-4 border-t border-gray-200" />,
      table: ({ children }) => (
        <div className="overflow-x-auto my-3 border border-gray-200 rounded-lg">
          <table className="min-w-full text-sm border-collapse">{children}</table>
        </div>
      ),
      thead: ({ children }) => <thead className="bg-gray-50">{children}</thead>,
      th: (props) => (
        <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700 border-b border-gray-200" {...props} />
      ),
      td: (props) => (
        <td className="px-3 py-2 text-sm text-gray-700 border-b border-gray-100 align-top" {...props} />
      ),
      pre: ({ children }) => (
        <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto my-3 text-xs font-mono leading-relaxed">
          {children}
        </pre>
      ),
      code: ({ className, children }) => {
        const isBlock = typeof className === 'string' && className.includes('language-');
        if (isBlock) {
          return <code className={className}>{children}</code>;
        }
        return (
          <code className="bg-gray-100 text-indigo-700 px-1.5 py-0.5 rounded text-xs font-mono">
            {children}
          </code>
        );
      },
    }}
  >
    {children}
  </ReactMarkdown>
);

export default Markdown;
