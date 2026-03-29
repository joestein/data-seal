import { useRef, useEffect } from 'react';
import { Rect, Group, Text, Transformer } from 'react-konva';
import type { KonvaEventObject } from 'konva/lib/Node';
import Konva from 'konva';
import { FIELD_TYPE_LABELS, RECIPIENT_COLORS } from '../../lib/constants';
import type { DocumentField, Recipient } from '../../api/types';

interface DraggableFieldProps {
  field: DocumentField;
  recipients: Recipient[];
  stageWidth: number;
  stageHeight: number;
  selected: boolean;
  onSelect: (fieldId: string) => void;
  onDragEnd: (fieldId: string, xPct: number, yPct: number) => void;
  onResizeEnd: (fieldId: string, xPct: number, yPct: number, wPct: number, hPct: number) => void;
}

export function DraggableField({
  field,
  recipients,
  stageWidth,
  stageHeight,
  selected,
  onSelect,
  onDragEnd,
  onResizeEnd,
}: DraggableFieldProps) {
  const shapeRef = useRef<Konva.Rect>(null);
  const trRef = useRef<Konva.Transformer>(null);

  const recipientIdx = recipients.findIndex((r) => r.id === field.recipient_id);
  const color = RECIPIENT_COLORS[recipientIdx % RECIPIENT_COLORS.length] || '#3b82f6';

  const x = (field.x_position / 100) * stageWidth;
  const y = (field.y_position / 100) * stageHeight;
  const w = (field.width / 100) * stageWidth;
  const h = (field.height / 100) * stageHeight;

  useEffect(() => {
    if (selected && trRef.current && shapeRef.current) {
      trRef.current.nodes([shapeRef.current]);
      trRef.current.getLayer()?.batchDraw();
    }
  }, [selected]);

  const handleDragEnd = (e: KonvaEventObject<DragEvent>) => {
    const node = e.target;
    const xPct = (node.x() / stageWidth) * 100;
    const yPct = (node.y() / stageHeight) * 100;
    onDragEnd(field.id, Math.max(0, Math.min(100, xPct)), Math.max(0, Math.min(100, yPct)));
  };

  const handleTransformEnd = () => {
    const node = shapeRef.current;
    if (!node) return;
    const scaleX = node.scaleX();
    const scaleY = node.scaleY();

    node.scaleX(1);
    node.scaleY(1);

    const newW = Math.max(5, node.width() * scaleX);
    const newH = Math.max(5, node.height() * scaleY);

    const xPct = (node.x() / stageWidth) * 100;
    const yPct = (node.y() / stageHeight) * 100;
    const wPct = (newW / stageWidth) * 100;
    const hPct = (newH / stageHeight) * 100;

    node.width(newW);
    node.height(newH);

    onResizeEnd(
      field.id,
      Math.max(0, Math.min(100, xPct)),
      Math.max(0, Math.min(100, yPct)),
      Math.max(1, Math.min(100, wPct)),
      Math.max(1, Math.min(100, hPct)),
    );
  };

  return (
    <>
      <Group>
        <Rect
          ref={shapeRef}
          x={x}
          y={y}
          width={w}
          height={h}
          fill={color + '20'}
          stroke={color}
          strokeWidth={selected ? 2 : 1}
          cornerRadius={2}
          draggable
          onClick={() => onSelect(field.id)}
          onTap={() => onSelect(field.id)}
          onDragEnd={handleDragEnd}
          onTransformEnd={handleTransformEnd}
        />
        <Text
          x={x + 4}
          y={y + 2}
          text={FIELD_TYPE_LABELS[field.type]}
          fontSize={10}
          fill={color}
          listening={false}
          width={w - 8}
        />
      </Group>
      {selected && (
        <Transformer
          ref={trRef}
          boundBoxFunc={(_oldBox, newBox) => {
            if (newBox.width < 20 || newBox.height < 10) return _oldBox;
            return newBox;
          }}
          rotateEnabled={false}
          flipEnabled={false}
        />
      )}
    </>
  );
}
