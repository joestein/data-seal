import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Modal } from '../../components/common/Modal';

function renderModal(props: Partial<React.ComponentProps<typeof Modal>> = {}) {
  return render(
    <Modal
      open={true}
      onClose={vi.fn()}
      title="Test Modal"
      {...props}
    >
      <p>Modal content</p>
    </Modal>,
  );
}

describe('Modal', () => {
  it('should render when open is true', () => {
    renderModal({ open: true });
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('should not render when open is false', () => {
    renderModal({ open: false });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderModal({ onClose });
    await user.click(screen.getByRole('button', { name: 'Close' }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('should call onClose when Escape key is pressed', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderModal({ onClose });
    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('should have aria-modal attribute', () => {
    renderModal();
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
  });

  it('should display the title as aria-label', () => {
    renderModal({ title: 'Confirm Delete' });
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-label', 'Confirm Delete');
  });

  it('should set body overflow hidden when open', () => {
    renderModal({ open: true });
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('should restore body overflow when closed', () => {
    const { rerender } = render(
      <Modal open={true} onClose={vi.fn()} title="Test">
        content
      </Modal>,
    );
    rerender(
      <Modal open={false} onClose={vi.fn()} title="Test">
        content
      </Modal>,
    );
    expect(document.body.style.overflow).toBe('');
  });
});
