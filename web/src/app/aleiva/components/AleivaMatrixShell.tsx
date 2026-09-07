"use client";

import { cn } from "@opal/utils";
import type { HtmlHTMLAttributes } from "react";

export interface AleivaMatrixShellProps extends HtmlHTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

/**
 * Matrix-inspired surface wrapper for Aleiva dashboard sections.
 * Uses high-contrast accent borders on existing design tokens.
 */
export function AleivaMatrixShell({
  children,
  className,
  ...props
}: AleivaMatrixShellProps) {
  return (
    <div
      className={cn(
        "relative rounded-16 border border-status-success-03/40",
        "bg-linear-to-br from-background-tint-01 via-background-tint-00 to-background-tint-01",
        "shadow-[inset_0_1px_0_0_rgba(74,222,128,0.08)]",
        "before:pointer-events-none before:absolute before:inset-0 before:rounded-16",
        "before:bg-[linear-gradient(rgba(74,222,128,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(74,222,128,0.03)_1px,transparent_1px)]",
        "before:bg-size-[1.25rem_1.25rem]",
        className
      )}
      {...props}
    >
      <div className="relative z-10">{children}</div>
    </div>
  );
}
