import { Link } from "react-router-dom";
import { useBehindTarget } from "@/api/queries/dashboard";
import Alert from "@/components/ui/Alert";
import PeriodProgress from "./PeriodProgress";

// Who to chase: creators behind target this period on any live campaign (US-22).
export default function BehindTargetList() {
  const behind = useBehindTarget();

  if (behind.isError) return <Alert>{behind.error.message}</Alert>;
  if (!behind.data || behind.data.length === 0) return null;

  return (
    <section className="rounded-xl border border-red-200 bg-white shadow-sm" aria-labelledby="behind-heading">
      <h2 id="behind-heading" className="border-b border-red-100 px-4 py-3 text-sm font-semibold text-gray-900">
        <span aria-hidden="true" className="mr-1.5 text-behind">
          !
        </span>
        Behind target this period ({behind.data.length})
      </h2>
      <ul className="divide-y divide-gray-100">
        {behind.data.map((item) => (
          <li
            key={`${item.campaign_id}-${item.creator.id}`}
            className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3"
          >
            <div className="min-w-0 flex-1">
              <Link
                to={`/creators/${item.creator.id}`}
                className="block truncate font-medium text-gray-900 hover:text-brand"
              >
                {item.creator.name}
              </Link>
              <p className="truncate text-sm text-gray-500">
                <Link to={`/campaigns/${item.campaign_id}`} className="hover:text-gray-900">
                  {item.campaign_name}
                </Link>{" "}
                · {item.remaining} more this {item.target_period}
              </p>
            </div>
            <PeriodProgress progress={item} />
            {item.email && (
              <a href={`mailto:${item.email}`} className="text-sm text-brand underline-offset-4 hover:underline">
                Email
              </a>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
