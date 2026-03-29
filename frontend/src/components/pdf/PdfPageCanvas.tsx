import { useState, useRef, useEffect, useCallback } from 'react';
import { Stage, Layer, Image as KonvaImage } from 'react-konva';
import { DraggableField } from '../fields/DraggableField';
import { FIELD_DEFAULT_SIZES } from '../../lib/constants';
import type { DocumentField, FieldType, Recipient } from '../../api/types';
import { useAuthStore } from '../../stores/authStore';

interface PdfPageCanvasProps {
  imageUrl: string;
  fields: DocumentField[];
  recipients: Recipient[];
  selectedFieldId: string | null;
  onSelectField: (fieldId: string | null) => void;
  onFieldDragEnd: (fieldId: string, xPct: number, yPct: number) => void;
  onFieldResizeEnd: (fieldId: string, xPct: number, yPct: number, wPct: number, hPct: number) => void;
  onDropNewField: (type: FieldType, xPct: number, yPct: number) => void;
  draggingFieldType: FieldType | null;
}

export function PdfPageCanvas({
  imageUrl,
  fields,
  recipients,
  selectedFieldId,
  onSelectField,
  onFieldDragEnd,
  onFieldResizeEnd,
  onDropNewField,
  draggingFieldType,
}: PdfPageCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 1100 });
  const { accessToken } = useAuthStore();

  useEffect(() => {
    const img = new window.Image();
    img.crossOrigin = 'anonymous';
    // Attach auth token via fetch and create object URL
    let objectUrl: string | null = null;
    let cancelled = false;

    fetch(imageUrl, {
      headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
    })
      .then((res) => res.blob())
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        img.src = objectUrl;
        img.onload = () => {
          const containerWidth = containerRef.current?.clientWidth ?? 800;
          const scale = containerWidth / img.naturalWidth;
          setDimensions({
            width: containerWidth,
            height: img.naturalHeight * scale,
          });
          setImage(img);
        };
      });

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [imageUrl, accessToken]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!draggingFieldType || !containerRef.current) return;

      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const defaults = FIELD_DEFAULT_SIZES[draggingFieldType];
      const xPct = (x / dimensions.width) * 100 - defaults.width / 2;
      const yPct = (y / dimensions.height) * 100 - defaults.height / 2;

      onDropNewField(
        draggingFieldType,
        Math.max(0, Math.min(100 - defaults.width, xPct)),
        Math.max(0, Math.min(100 - defaults.height, yPct)),
      );
    },
    [draggingFieldType, dimensions, onDropNewField],
  );

  const handleStageClick = useCallback(
    (e: { target: { getStage: () => unknown } }) => {
      if (e.target === e.target.getStage()) {
        onSelectField(null);
      }
    },
    [onSelectField],
  );

  return (
    <div
      ref={containerRef}
      className="relative"
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <Stage
        width={dimensions.width}
        height={dimensions.height}
        onClick={handleStageClick}
        onTap={handleStageClick}
      >
        <Layer>
          {image && (
            <KonvaImage
              image={image}
              width={dimensions.width}
              height={dimensions.height}
            />
          )}
          {fields.map((field) => (
            <DraggableField
              key={field.id}
              field={field}
              recipients={recipients}
              stageWidth={dimensions.width}
              stageHeight={dimensions.height}
              selected={selectedFieldId === field.id}
              onSelect={onSelectField}
              onDragEnd={onFieldDragEnd}
              onResizeEnd={onFieldResizeEnd}
            />
          ))}
        </Layer>
      </Stage>
    </div>
  );
}
