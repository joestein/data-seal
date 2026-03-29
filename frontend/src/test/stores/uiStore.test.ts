import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { useUiStore } from '../../stores/uiStore';

beforeEach(() => {
  useUiStore.setState({ toasts: [] });
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('uiStore', () => {
  describe('initial state', () => {
    it('should have an empty toasts array', () => {
      expect(useUiStore.getState().toasts).toEqual([]);
    });
  });

  describe('addToast', () => {
    it('should add a toast with a generated id', () => {
      useUiStore.getState().addToast({ type: 'success', message: 'Saved!' });
      const { toasts } = useUiStore.getState();
      expect(toasts).toHaveLength(1);
      expect(toasts[0].type).toBe('success');
      expect(toasts[0].message).toBe('Saved!');
      expect(toasts[0].id).toMatch(/^toast-\d+$/);
    });

    it('should add multiple toasts with unique ids', () => {
      useUiStore.getState().addToast({ type: 'success', message: 'First' });
      useUiStore.getState().addToast({ type: 'error', message: 'Second' });
      const { toasts } = useUiStore.getState();
      expect(toasts).toHaveLength(2);
      expect(toasts[0].id).not.toBe(toasts[1].id);
    });

    it('should auto-remove toast after 5 seconds', () => {
      useUiStore.getState().addToast({ type: 'info', message: 'Temporary' });
      expect(useUiStore.getState().toasts).toHaveLength(1);
      vi.advanceTimersByTime(5000);
      expect(useUiStore.getState().toasts).toHaveLength(0);
    });

    it('should not remove toast before 5 seconds', () => {
      useUiStore.getState().addToast({ type: 'info', message: 'Temporary' });
      vi.advanceTimersByTime(4999);
      expect(useUiStore.getState().toasts).toHaveLength(1);
    });

    it('should support all toast types', () => {
      const types = ['success', 'error', 'info', 'warning'] as const;
      types.forEach((type) => {
        useUiStore.setState({ toasts: [] });
        useUiStore.getState().addToast({ type, message: `${type} message` });
        expect(useUiStore.getState().toasts[0].type).toBe(type);
      });
    });
  });

  describe('removeToast', () => {
    it('should remove toast by id', () => {
      useUiStore.getState().addToast({ type: 'success', message: 'Keep me' });
      useUiStore.getState().addToast({ type: 'error', message: 'Remove me' });
      const { toasts } = useUiStore.getState();
      const idToRemove = toasts[1].id;
      useUiStore.getState().removeToast(idToRemove);
      const remaining = useUiStore.getState().toasts;
      expect(remaining).toHaveLength(1);
      expect(remaining[0].message).toBe('Keep me');
    });

    it('should do nothing when id does not exist', () => {
      useUiStore.getState().addToast({ type: 'success', message: 'Hello' });
      useUiStore.getState().removeToast('nonexistent-id');
      expect(useUiStore.getState().toasts).toHaveLength(1);
    });
  });
});
