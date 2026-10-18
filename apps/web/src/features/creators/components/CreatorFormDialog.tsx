import { type Creator, useCreateCreator, useUpdateCreator } from "@/api/queries/creators";
import Modal from "@/components/ui/Modal";
import CreatorForm from "./CreatorForm";

interface CreatorFormDialogProps {
  open: boolean;
  /** Edit this creator; omit to add a new one. */
  creator?: Creator;
  onClose: () => void;
  onSaved?: (creator: Creator) => void;
}

export default function CreatorFormDialog({ open, creator, onClose, onSaved }: CreatorFormDialogProps) {
  const create = useCreateCreator();
  const update = useUpdateCreator();
  const mutation = creator ? update : create;

  function close() {
    create.reset();
    update.reset();
    onClose();
  }

  return (
    <Modal open={open} title={creator ? "Edit creator" : "Add creator"} onClose={close}>
      {/* Remount per creator so the form starts from its current values */}
      <CreatorForm
        key={creator?.id ?? "new"}
        creator={creator}
        submitLabel={creator ? "Save changes" : "Add creator"}
        pending={mutation.isPending}
        error={mutation.error?.message}
        onCancel={close}
        onSubmit={(values) => {
          const onSuccess = (saved: Creator) => {
            onSaved?.(saved);
            close();
          };
          if (creator) update.mutate({ id: creator.id, changes: values }, { onSuccess });
          else create.mutate(values, { onSuccess });
        }}
      />
    </Modal>
  );
}
