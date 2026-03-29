import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '../common/Button';

interface PdfViewerProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  children: React.ReactNode;
}

export function PdfViewer({ currentPage, totalPages, onPageChange, children }: PdfViewerProps) {
  return (
    <div className="flex flex-col">
      <div className="mb-2 flex items-center justify-center gap-3">
        <Button
          variant="secondary"
          size="sm"
          disabled={currentPage <= 1}
          onClick={() => onPageChange(currentPage - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-sm text-gray-700">
          Page {currentPage} of {totalPages}
        </span>
        <Button
          variant="secondary"
          size="sm"
          disabled={currentPage >= totalPages}
          onClick={() => onPageChange(currentPage + 1)}
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
      <div className="overflow-auto rounded-lg border border-gray-200 bg-gray-100 p-2">
        {children}
      </div>
    </div>
  );
}
