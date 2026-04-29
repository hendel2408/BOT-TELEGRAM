"use client";

import { useRef } from "react";
import Header from "@/components/Header";
import GalinhasLivresSequence from "@/components/GalinhasLivresSequence";

export default function GalinhasLivresPage() {
  const galinhaRef = useRef<HTMLImageElement | null>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (!galinhaRef.current) return;

    galinhaRef.current.style.opacity = "1";
    galinhaRef.current.style.transform = `translate(${x - 40}px, ${y - 40}px)`;
  };

  const handleMouseLeave = () => {
    if (!galinhaRef.current) return;
    galinhaRef.current.style.opacity = "0";
  };

  const instagramPosts = [
    {
      image: "/insta/galinhalivre6.jpg",
      link: "https://www.instagram.com/ovoscampoverde/",
      alt: "Post Instagram Campo Verde - Galinhas livres 1",
    },
    {
      image: "/insta/galinhalivre5.jpg",
      link: "https://www.instagram.com/p/DVQrUJkjYV7/",
      alt: "Post Instagram Campo Verde - Dia da saúde",
    },
    {
      image: "/insta/galinhalivre3.jpg",
      link: "https://www.instagram.com/p/DVn8x6TjYAn/",
      alt: "Post Instagram Campo Verde - Dia do consumidor",
    },
    {
      image: "/insta/galinhalivre4.jpg",
      link: "https://www.instagram.com/p/DUsoLbxj5ZT/",
      alt: "Post Instagram Campo Verde - Ovos de qualidade",
    },
    {
      image: "/insta/galinhalivre1.jpg",
      link: "https://www.instagram.com/p/DUl2LBJgS16/",
      alt: "Post Instagram Campo Verde - Poder dos ovos de codorna",
    },
    {
      image: "/insta/galinhalivre0.jpg",
      link: "https://www.instagram.com/p/DUk52dWCDa4/",
      alt: "Post Instagram Campo Verde - Receita especial",
    },
  ];

  return (
    <main className="gl-page">
      <Header />

      <GalinhasLivresSequence />

      <div
        className="gl-area-com-galinha"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <section className="container-p pt-20 pb-16 gl-livres-content">
  <div className="gl-top-layout">

    {/* IMAGEM NOVA */}
    <div className="gl-left-image">
      <img
        src="/galinhas-livres-home.png"
        alt="Galinhas livres"
        className="gl-feature-img"
      />
    </div>

    {/* ÍCONES */}
    <div className="gl-icons">
      <div className="gl-icons-content">
        <div className="gl-icons-header">
          <h2 className="gl-icons-title">
  <span className="gl-title-line-1">Ovos de galinhas criadas</span>
  <span className="gl-title-line-2">Livres de gaiolas</span>
</h2>
          <p className="gl-icons-text">
            A produção de ovos no formato livres de gaiola preza pelo bem-estar
            das nossas galinhas e também pela segurança e qualidade dos nossos ovos.
          </p>
        </div>

        <img src="/icones2.png" alt="" className="gl-icons-img" />
      </div>
    </div>
    <div className="gl-right-image">
  <img
    src="/produtolivre.png"
    alt="Produto ovos livres"
    className="gl-product-img"
  />
</div>

  </div>
</section>

        <section className="cv-insta-strip gl-insta-section">
          <div className="container-p">
            <div className="cv-insta-header">
              <h2 className="cv-insta-title">Veja Mais das Nossas Galinhas !</h2>
              <p className="cv-insta-subtitle">
                Veja novidades, bastidores da produção das galinhas livres e conteúdos da nossa
                granja.
              </p>
            </div>
          </div>

          <div className="cv-insta-marquee">
            <div className="cv-insta-track">
              {[...instagramPosts, ...instagramPosts].map((post, index) => (
                <a
                  key={index}
                  href={post.link}
                  target="_blank"
                  rel="noreferrer"
                  className="cv-insta-card"
                >
                  <img
                    src={post.image}
                    alt={post.alt}
                    className="cv-insta-image"
                  />
                  <div className="cv-insta-overlay">
                    <span className="cv-insta-icon"></span>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </section>
      </div>

      <footer className="cv-footer-main">
        <svg
          className="cv-footer-wave"
          viewBox="0 0 1440 220"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="footerGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#FF6A00" />
              <stop offset="100%" stopColor="#fca345" />
            </linearGradient>
          </defs>

          <path
            fill="url(#footerGradient)"
            d="M0,80C120,40,240,30,360,45C480,60,600,110,720,105C840,100,960,40,1080,30C1200,20,1320,60,1440,95L1440,220L0,220Z"
          >
            <animate
              attributeName="d"
              dur="5s"
              repeatCount="indefinite"
              values="
                M0,80C120,40,240,30,360,45C480,60,600,110,720,105C840,100,960,40,1080,30C1200,20,1320,60,1440,95L1440,220L0,220Z;
                M0,95C120,70,240,35,360,30C480,25,600,70,720,90C840,110,960,95,1080,70C1200,45,1320,35,1440,55L1440,220L0,220Z;
                M0,80C120,40,240,30,360,45C480,60,600,110,720,105C840,100,960,40,1080,30C1200,20,1320,60,1440,95L1440,220L0,220Z
              "
            />
          </path>
        </svg>

        <div className="cv-footer-container">
          <div className="cv-footer-brand">
            <img
              src="verde.png"
              alt="Campo Verde"
              className="cv-footer-logo"
            />

            <div className="cv-footer-social">
              <a
                href="https://www.facebook.com/granjacampoverde?locale=pt_BR"
                target="_blank"
                rel="noreferrer"
                aria-label="Facebook"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="currentColor"
                    d="M22 12.07C22 6.48 17.52 2 12 2S2 6.48 2 12.07c0 4.99 3.66 9.13 8.44 9.93v-7.03H7.9v-2.9h2.54V9.8c0-2.5 1.49-3.88 3.78-3.88 1.09 0 2.24.19 2.24.19v2.47h-1.26c-1.24 0-1.63.77-1.63 1.56v1.87h2.77l-.44 2.9h-2.33V22c4.78-.8 8.43-4.94 8.43-9.93z"
                  />
                </svg>
              </a>

              <a
                href="https://www.instagram.com/ovoscampoverde/"
                target="_blank"
                rel="noreferrer"
                aria-label="Instagram"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="currentColor"
                    d="M7 2C4.24 2 2 4.24 2 7v10c0 2.76 2.24 5 5 5h10c2.76 0 5-2.24 5-5V7c0-2.76-2.24-5-5-5H7zm5 3.5A6.5 6.5 0 1112 18.5 6.5 6.5 0 0112 5.5zm6.5-.88a1.12 1.12 0 110 2.24 1.12 1.12 0 010-2.24zM12 8a4 4 0 100 8 4 4 0 000-8z"
                  />
                </svg>
              </a>

              <a
                href="https://www.tiktok.com/@ovoscampoverde"
                target="_blank"
                rel="noreferrer"
                aria-label="TikTok"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="currentColor"
                    d="M12 2h3a5 5 0 005 5v3a8 8 0 01-4-1.1v6.6a6.5 6.5 0 11-6.5-6.5h1.2v3h-1.2a3.5 3.5 0 103.5 3.5V2z"
                  />
                </svg>
              </a>

              <a
                href="https://www.linkedin.com/company/granjacampoverde/posts/?feedView=all"
                target="_blank"
                rel="noreferrer"
                aria-label="LinkedIn"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="currentColor"
                    d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1s2.48 1.12 2.48 2.5zM0 8h5v16H0zM8 8h4.8v2.3h.07c.67-1.27 2.3-2.6 4.73-2.6C22 7.7 24 10.3 24 14.2V24h-5v-8.6c0-2-.04-4.6-2.8-4.6-2.8 0-3.2 2.2-3.2 4.5V24H8z"
                  />
                </svg>
              </a>
            </div>
          </div>

          <div className="cv-footer-links">
            <h4>A GRANJA</h4>
            <a href="/">Home</a>
            <a href="/quem-somos">Quem somos</a>
            <a href="/produtos">Produtos</a>
            <a href="/blog">Blog</a>
            <a href="/galinhas-livres">Galinhas livres</a>
            <a href="#">Trabalhe conosco</a>
            <a href="/contato">Contato</a>
            <a href="#">Wiki</a>
          </div>

          <div className="cv-footer-contact">
            <h4>CONTATO</h4>
            <p>BR 070 Km 373 – Campo Verde/MT</p>
            <p>(66) 3419-1271</p>
            <p>https://www.ovoscampoverde.com.br/</p>
          </div>
        </div>

        <div className="cv-footer-bottom">
          Feito com carinho por <span>Agência de sites</span>
        </div>
      </footer>
    </main>
  );
}