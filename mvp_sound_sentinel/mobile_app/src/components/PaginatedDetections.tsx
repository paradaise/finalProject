import { useState, useEffect } from 'react';
import { Volume2, Clock, ChevronLeft, ChevronRight } from 'lucide-react';

interface Detection {
  id: string;
  sound_type: string;
  confidence: number;
  timestamp: string;
}

interface Props {
  detections: Detection[];
  getSoundIcon: (sound: string) => string;
}

export function PaginatedDetections({ detections, getSoundIcon }: Props) {
  const [currentPage, setCurrentPage] = useState(1);
  const [paginatedDetections, setPaginatedDetections] = useState<Detection[]>([]);
  const itemsPerPage = 50;
  const totalPages = Math.ceil(detections.length / itemsPerPage);

  useEffect(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    setPaginatedDetections(detections.slice(startIndex, endIndex));
  }, [currentPage, detections]);

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'text-green-600 bg-green-50';
    if (confidence > 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  if (detections.length === 0) {
    return (
      <div className="bg-white rounded-xl p-8 text-center shadow-sm">
        <Volume2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500 text-lg">Нет детекций</p>
        <p className="text-gray-400 text-sm mt-2">Звуки еще не были обнаружены</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Volume2 className="w-5 h-5" />
            Детекции звука
          </h3>
          <div className="text-sm">
            Всего: {detections.length} | Страница {currentPage} из {totalPages}
          </div>
        </div>
      </div>

      {/* Detections List */}
      <div className="max-h-96 overflow-y-auto">
        {paginatedDetections.map((detection, index) => (
          <div
            key={detection.id}
            className={`p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
              index === 0 ? 'bg-blue-50' : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                <span className="text-2xl mt-1">{getSoundIcon(detection.sound_type)}</span>
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900 text-lg">
                    {detection.sound_type}
                    {index === 0 && (
                      <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-600 text-xs rounded-full">
                        Последнее
                      </span>
                    )}
                  </h4>
                  <div className="flex items-center gap-4 mt-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(detection.confidence)}`}>
                      {(detection.confidence * 100).toFixed(1)}%
                    </span>
                    <div className="flex items-center gap-1 text-gray-500 text-sm">
                      <Clock className="w-4 h-4" />
                      {formatTime(detection.timestamp)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-gray-50 border-t border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Назад
            </button>

            <div className="flex items-center gap-2">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => goToPage(pageNum)}
                    className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                      currentPage === pageNum
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Вперед
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
