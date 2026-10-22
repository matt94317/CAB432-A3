import { type Creator, useDeleteCreator } from "@/api/queries/creators";
import ConfirmDialog from "@/components/ui/ConfirmDialog";

interface DeleteCreatorDialogProps {
  creator?: Creator;
  onClose: () => void;
  onDeleted?: () => void;
}

// Confirm removing a creator from the roster (US-08).
export default function DeleteCreatorDialog({ creator, onClose, onDeleted }: DeleteCreatorDialogProps) {
  const remove = useDeleteCreator();
  const campaigns = creator?.campaign_count ?? 0;

  function close() {
    remove.reset();
    onClose();
  }

  return (
    <ConfirmDialog
      open={creator !== undefined}
      title="Remove creator?"
      confirmLabel="Remove creator"
      danger
      pending={remove.isPending}
      error={remove.error?.message}
      onCancel={close}
      onConfirm={() =>
        creator &&
        remove.mutate(creator.id, {
          onSuccess: () => {
            close();
            onDeleted?.();
          },
        })
      }
    >
      <p>
        <span className="font-medium text-ink">{creator?.name}</span> and their tracked posts will be removed
        from your roster.
        {campaigns > 0 &&
          ` They'll also be taken off ${campaigns === 1 ? "the 1 campaign" : `all ${campaigns} campaigns`} they're assigned to.`}
      </p>
    </ConfirmDialog>
  );
}
