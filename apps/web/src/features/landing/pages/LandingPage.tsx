import CustomerStory from "../components/CustomerStory";
import Faq from "../components/Faq";
import FinalInvitation from "../components/FinalInvitation";
import Hero from "../components/Hero";
import LandingFooter from "../components/LandingFooter";
import LandingNav from "../components/LandingNav";
import Pricing from "../components/Pricing";
import ProductShowcase from "../components/ProductShowcase";
import Relationships from "../components/Relationships";
import TrustedBrands from "../components/TrustedBrands";
import Workflow from "../components/Workflow";
import { Container } from "../components/shared";

// Public home page at "/", from the "Landing page" frame of the Hookd Figma file.
export default function LandingPage() {
  return (
    <div className="min-h-screen overflow-x-clip bg-canvas">
      <LandingNav />
      <main>
        <Hero />
        <TrustedBrands />
        <Workflow />
        <ProductShowcase />
        <Relationships />
        <CustomerStory />
        <Container className="flex flex-col gap-[68px] pb-20 pt-16 lg:pt-[88px]">
          <Pricing />
          <Faq />
        </Container>
        <FinalInvitation />
      </main>
      <LandingFooter />
    </div>
  );
}
