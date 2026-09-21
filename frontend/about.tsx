import { useMemo, useRef, type CSSProperties, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { motion, useReducedMotion, useScroll, useTransform, type MotionValue } from "framer-motion";

type FadeInProps = {
  children: ReactNode;
  delay?: number;
  duration?: number;
  x?: number;
  y?: number;
  className?: string;
  style?: CSSProperties;
  as?: keyof HTMLElementTagNameMap;
};

export function FadeIn({
  children, delay = 0, duration = 0.7, x = 0, y = 30,
  className, style, as = "div",
}: FadeInProps) {
  const reducedMotion = useReducedMotion();
  const Component = useMemo(() => motion.create(as), [as]);

  return (
    <Component
      className={className}
      style={style}
      initial={reducedMotion ? false : "hidden"}
      whileInView="visible"
      viewport={{ once: true, margin: "50px", amount: 0 }}
      variants={{
        hidden: { opacity: 0, x, y },
        visible: { opacity: 1, x: 0, y: 0 },
      }}
      transition={{ delay: reducedMotion ? 0 : delay, duration: reducedMotion ? 0 : duration, ease: [0.25, 0.1, 0.25, 1] }}
    >
      {children}
    </Component>
  );
}

function Character({ character, index, count, progress }: {
  character: string;
  index: number;
  count: number;
  progress: MotionValue<number>;
}) {
  const charProgress = index / count;
  const opacity = useTransform(progress,
    [Math.max(0, charProgress - 0.1), Math.min(1, charProgress + 0.05)],
    [0.2, 1]);
  const displayCharacter = /\s/.test(character) ? "\u00a0" : character;

  return (
    <span className="about-character">
      <span className="about-character__space">{displayCharacter}</span>
      <motion.span className="about-character__visible" style={{ opacity }}>{displayCharacter}</motion.span>
    </span>
  );
}

function AnimatedBio({ text }: { text: string }) {
  const containerRef = useRef<HTMLParagraphElement>(null);
  const reducedMotion = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start 0.8", "end 0.2"] });
  const words = text.match(/\S+\s*/gu) ?? [];
  const totalChars = Array.from(text).length;
  let characterIndex = 0;

  return (
    <p ref={containerRef} className="about-bio tw-max-w-[560px] tw-text-center tw-font-medium tw-leading-relaxed">
      {reducedMotion ? text : <>
        <span className="tw-sr-only">{text}</span>
        <span aria-hidden="true">
          {words.map((word, wordIndex) => (
            <span className="about-word" key={wordIndex}>
              {Array.from(word).map((character) => {
                const index = characterIndex++;
                return <Character key={index} character={character} index={index} count={totalChars} progress={scrollYProgress} />;
              })}
            </span>
          ))}
        </span>
      </>}
    </p>
  );
}

type AboutProps = { name: string; bio: string; moon: string; object: string; lego: string; group: string };

function About({ name, bio, moon, object, lego, group }: AboutProps) {
  const decorations = [
    { name: "moon", src: moon, delay: 0.1, x: -80, size: 210 },
    { name: "object", src: object, delay: 0.25, x: -80, size: 180 },
    { name: "lego", src: lego, delay: 0.15, x: 80, size: 210 },
    { name: "group", src: group, delay: 0.3, x: 80, size: 220 },
  ];

  return <>
    {decorations.map(({ name, src, delay, x, size }) => (
      <FadeIn key={name} className={`about-decoration about-decoration--${name}`} delay={delay} duration={0.9} x={x} y={0}>
        <img src={src} alt="" aria-hidden="true" width={size} height={size} draggable={false} />
      </FadeIn>
    ))}
    <div className="about-content tw-relative tw-z-10 tw-mx-auto tw-flex tw-w-full tw-max-w-4xl tw-flex-col tw-items-center tw-gap-16 sm:tw-gap-20 md:tw-gap-24">
      <div className="about-introduction tw-flex tw-w-full tw-flex-col tw-items-center tw-gap-10 sm:tw-gap-14 md:tw-gap-16">
        <FadeIn delay={0} y={40} className="tw-w-full">
          <h1 className="about-heading hero-heading tw-text-center tw-font-black tw-uppercase tw-leading-none tw-tracking-tight" id="about-heading">{name}</h1>
        </FadeIn>
        <AnimatedBio text={bio} />
      </div>
      <FadeIn delay={0.3} y={20}>
        <a className="about-contact-button tw-inline-flex tw-items-center tw-justify-center tw-rounded-full tw-px-8 tw-py-3 tw-text-xs tw-font-medium tw-uppercase tw-tracking-widest sm:tw-px-10 sm:tw-py-3.5 sm:tw-text-sm md:tw-px-12 md:tw-py-4 md:tw-text-base" href="#contact">Contact Me</a>
      </FadeIn>
    </div>
  </>;
}

const mount = document.getElementById("about-app");
if (mount) {
  const { name, bio, moon, object, lego, group } = mount.dataset;
  // Keep Django's complete, accessible fallback if any required data is absent.
  if (name && bio && moon && object && lego && group) {
    createRoot(mount).render(<About name={name} bio={bio} moon={moon} object={object} lego={lego} group={group} />);
  }
}
