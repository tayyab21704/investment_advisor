import { cn } from '@/lib/utils';
import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    children?: React.ReactNode;
    hover?: boolean;
}

export const Card = ({ children, className, hover = true, ...props }: CardProps) => {
    return (
        <div
            className={cn(
                "bg-bg-surface border border-border-default rounded-lg p-5 transition-all duration-fast ease-out-expo",
                hover && "hover:border-border-strong hover:bg-bg-elevated",
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
};
