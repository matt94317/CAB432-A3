import { Container } from "./shared";

const BRANDS = [
  { name: "forma", bold: true },
  { name: "DAYBREAK", bold: false },
  { name: "morrow®", bold: true },
  { name: "offscript", bold: false },
  { name: "wildkind", bold: true },
  { name: "SUNDAY CLUB", bold: false },
];

export default function TrustedBrands() {
  return (
    <section aria-label="Brands using Hookd" className="border-y border-line">
      <Container className="flex flex-col gap-7 pb-12 pt-7 xl:px-[100px]">
        <p className="text-center text-[11px] leading-[1.45] text-ink-muted">GOOD COMPANY. GREAT COLLABORATIONS.</p>
        <ul className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4 text-[#69636f] lg:justify-between">
          {BRANDS.map((brand) => (
            <li key={brand.name} className={brand.bold ? "text-[27px] font-bold" : "text-[19px]"}>
              {brand.name}
            </li>
          ))}
        </ul>
      </Container>
    </section>
  );
}
