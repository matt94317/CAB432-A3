import { type Campaign, useCreateCampaign, useUpdateCampaign } from "@/api/queries/campaigns";
import Modal from "@/components/ui/Modal";
import CampaignForm from "./CampaignForm";

interface CampaignFormDialogProps {
  open: boolean;
  /** Edit this campaign; omit to create a new one. */
  campaign?: Campaign;
  onClose: () => void;
  onSaved?: (campaign: Campaign) => void;
}

export default function CampaignFormDialog({ open, campaign, onClose, onSaved }: CampaignFormDialogProps) {
  const create = useCreateCampaign();
  const update = useUpdateCampaign();
  const mutation = campaign ? update : create;

  function close() {
    create.reset();
    update.reset();
    onClose();
  }

  return (
    <Modal open={open} title={campaign ? "Edit campaign" : "New campaign"} onClose={close}>
      {/* Remount per campaign so the form starts from its current values */}
      <CampaignForm
        key={campaign?.id ?? "new"}
        campaign={campaign}
        submitLabel={campaign ? "Save changes" : "Create campaign"}
        pending={mutation.isPending}
        error={mutation.error?.message}
        onCancel={close}
        onSubmit={(values) => {
          const onSuccess = (saved: Campaign) => {
            onSaved?.(saved);
            close();
          };
          if (campaign) update.mutate({ id: campaign.id, changes: values }, { onSuccess });
          else create.mutate(values, { onSuccess });
        }}
      />
    </Modal>
  );
}
