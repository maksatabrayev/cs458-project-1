import "./globals.css";
import Providers from "./providers";

export const metadata = {
  title: "ARES Auth - AI-Driven Resilient Authentication",
  description: "Autonomous Self-Healing Authentication & Adaptive Security System",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
