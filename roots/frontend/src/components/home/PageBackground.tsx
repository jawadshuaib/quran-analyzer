/** Arabesque corner ornaments — hidden on mobile, visible on md+ screens */
export default function PageBackground() {
  return (
    <>
      <img
        src="/arabesque-corner.png"
        alt=""
        aria-hidden="true"
        className="hidden md:block fixed top-0 left-0 w-[300px] h-auto pointer-events-none z-0 opacity-35"
      />
      <img
        src="/arabesque-corner.png"
        alt=""
        aria-hidden="true"
        className="hidden md:block fixed top-0 right-0 w-[300px] h-auto pointer-events-none z-0 opacity-35 -scale-x-100"
      />
    </>
  );
}
