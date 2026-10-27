"""PolarCompress | PolarLabs-OSS - batch image optimizer."""
from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageOps

BG="#091623"; PANEL="#122537"; FG="#EAF6FA"; ACC="#27D6D0"; MUTED="#9BB5C2"
SUPPORTED={".jpg",".jpeg",".png",".webp",".bmp",".tif",".tiff"}

def convert_image(source, destination, fmt="WEBP", quality=82, max_width=0, max_height=0):
    source=Path(source); destination=Path(destination)
    if source.resolve()==destination.resolve():
        raise ValueError("Output uguale all'originale")
    with Image.open(source) as im:
        im=ImageOps.exif_transpose(im)
        im.load()
        if max_width or max_height:
            width=max_width or im.width
            height=max_height or im.height
            im.thumbnail((width,height),Image.Resampling.LANCZOS)
        fmt=fmt.upper()
        if fmt=="JPEG":
            if im.mode in ("RGBA","LA") or (im.mode=="P" and "transparency" in im.info):
                rgba=im.convert("RGBA")
                bg=Image.new("RGB",rgba.size,"white")
                bg.paste(rgba,mask=rgba.getchannel("A"))
                im=bg
            else:
                im=im.convert("RGB")
        elif fmt=="WEBP" and im.mode not in ("RGB","RGBA"):
            im=im.convert("RGBA" if "A" in im.getbands() else "RGB")
        elif fmt=="PNG" and im.mode not in ("RGB","RGBA","L","LA","P"):
            im=im.convert("RGBA")
        destination.parent.mkdir(parents=True,exist_ok=True)
        save={"format":fmt}
        if fmt=="JPEG":save.update(quality=quality,optimize=True,progressive=True)
        elif fmt=="WEBP":save.update(quality=quality,method=5)
        elif fmt=="PNG":save.update(optimize=True,compress_level=9)
        im.save(destination,**save)
    return source.stat().st_size,destination.stat().st_size

def unique_output(folder, stem, extension, reserved):
    candidate=folder/(stem+extension);i=2
    while candidate.exists() or candidate in reserved:
        candidate=folder/(f"{stem}_{i}"+extension);i+=1
    reserved.add(candidate)
    return candidate

class App:
    def __init__(self,root):
        self.root=root;root.title("PolarCompress | PolarLabs-OSS");root.geometry("1020x720");root.configure(bg=BG)
        self.paths=[];self.running=False;self.stop_event=threading.Event()
        main=tk.Frame(root,bg=BG,padx=25,pady=20);main.pack(fill="both",expand=True)
        tk.Label(main,text="POLAR / COMPRESS",bg=BG,fg=ACC,font=("Segoe UI",25,"bold")).pack(anchor="w")
        tk.Label(main,text="Ottimizza e converti immagini in locale • Gli originali non vengono modificati",bg=BG,fg=MUTED).pack(anchor="w",pady=(0,15))
        buttons=tk.Frame(main,bg=BG);buttons.pack(fill="x")
        for label,fn in [("+ Aggiungi immagini",self.add),("Aggiungi cartella",self.add_folder),("Svuota",self.clear)]:
            self.button(buttons,label,fn).pack(side="left",padx=(0,8))
        panel=tk.Frame(main,bg=PANEL,padx=15,pady=13);panel.pack(fill="x",pady=15)
        upper=tk.Frame(panel,bg=PANEL);upper.pack(fill="x",pady=5)
        tk.Label(upper,text="Formato:",fg=FG,bg=PANEL).pack(side="left")
        self.fmt=tk.StringVar(value="WebP")
        ttk.Combobox(upper,values=("WebP","JPEG","PNG"),textvariable=self.fmt,state="readonly",width=10).pack(side="left",padx=(8,20))
        tk.Label(upper,text="Qualità:",fg=FG,bg=PANEL).pack(side="left")
        self.quality=tk.IntVar(value=82)
        tk.Scale(upper,from_=35,to=100,orient="horizontal",variable=self.quality,bg=PANEL,fg=FG,highlightthickness=0,length=180).pack(side="left")
        tk.Label(upper,text="(JPEG/WebP)",fg=MUTED,bg=PANEL).pack(side="left",padx=7)
        lower=tk.Frame(panel,bg=PANEL);lower.pack(fill="x",pady=6)
        self.width=tk.StringVar(value="0");self.height=tk.StringVar(value="0")
        for title,var in (("Larghezza max:",self.width),("Altezza max:",self.height)):
            tk.Label(lower,text=title,fg=FG,bg=PANEL).pack(side="left",padx=(0,7))
            tk.Entry(lower,textvariable=var,width=8,bg=BG,fg=FG,insertbackground=FG).pack(side="left",padx=(0,24),ipady=4)
        tk.Label(lower,text="0 = originale",fg=MUTED,bg=PANEL).pack(side="left")
        pathrow=tk.Frame(main,bg=BG);pathrow.pack(fill="x",pady=(0,12))
        self.folder=tk.StringVar(value="")
        tk.Label(pathrow,text="Destinazione:",bg=BG,fg=FG).pack(side="left")
        tk.Entry(pathrow,textvariable=self.folder,bg=PANEL,fg=FG,insertbackground=FG,relief="flat").pack(side="left",fill="x",expand=True,padx=10,ipady=7)
        self.button(pathrow,"Sfoglia",self.choose_folder).pack(side="left")
        style=ttk.Style();style.theme_use("clam")
        style.configure("Treeview",background=PANEL,foreground=FG,fieldbackground=PANEL,rowheight=27)
        style.configure("Treeview.Heading",background="#1B3850",foreground=FG)
        self.table=ttk.Treeview(main,columns=("file","original","output","saved","state"),show="headings")
        for key,label,w in (("file","Immagine",275),("original","Originale",110),("output","Output",110),("saved","Variazione",110),("state","Stato",150)):
            self.table.heading(key,text=label);self.table.column(key,width=w)
        self.table.pack(fill="both",expand=True)
        actions=tk.Frame(main,bg=BG);actions.pack(fill="x",pady=(14,4))
        self.button(actions,"Comprimi / Converti",self.start,primary=True).pack(side="left",padx=(0,9))
        self.button(actions,"Interrompi",self.cancel).pack(side="left")
        self.progress=ttk.Progressbar(main,mode="determinate");self.progress.pack(fill="x",pady=(12,5))
        self.status=tk.StringVar(value="Pronto");tk.Label(main,textvariable=self.status,fg=MUTED,bg=BG).pack(anchor="w")
        tk.Label(main,text="PolarLabs-OSS  •  Nessun cloud  •  Licenza MIT",fg=MUTED,bg=BG,font=("Segoe UI",8)).pack(anchor="w",pady=9)
    def button(self,parent,text,command,primary=False):
        return tk.Button(parent,text=text,command=command,bg=ACC if primary else PANEL,fg=BG if primary else FG,relief="flat",padx=13,pady=8)
    def add_paths(self,paths):
        if self.running:return
        for p in paths:
            p=Path(p)
            if p.is_file() and p.suffix.lower() in SUPPORTED and p not in self.paths:
                self.paths.append(p)
                self.table.insert("","end",iid=str(len(self.paths)-1),values=(p.name,self.size(p.stat().st_size),"—","—","In attesa"))
        self.status.set(f"{len(self.paths)} immagini selezionate")
    def add(self):self.add_paths(filedialog.askopenfilenames(filetypes=[("Immagini","*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff")]))
    def add_folder(self):
        p=filedialog.askdirectory()
        if p:self.add_paths(x for x in Path(p).iterdir() if x.is_file())
    def choose_folder(self):
        p=filedialog.askdirectory()
        if p:self.folder.set(p)
    def clear(self):
        if self.running:return
        self.paths=[]
        for item in self.table.get_children():self.table.delete(item)
        self.progress["value"]=0;self.status.set("Elenco svuotato")
    def cancel(self):self.stop_event.set()
    @staticmethod
    def size(n):return f"{n/1024:.1f} KB" if n<1048576 else f"{n/1048576:.2f} MB"
    def start(self):
        if self.running or not self.paths:return
        try:
            w=int(self.width.get());h=int(self.height.get())
            if w<0 or h<0 or w>100000 or h>100000:raise ValueError()
        except ValueError:return messagebox.showerror("PolarCompress","Dimensioni non valide")
        target=self.folder.get().strip()
        if not target:return messagebox.showwarning("PolarCompress","Seleziona prima la cartella di destinazione")
        dest=Path(target)
        if not dest.is_dir():return messagebox.showerror("PolarCompress","Cartella di destinazione inesistente")
        fmt=self.fmt.get().upper();q=self.quality.get()
        ext={"WEBP":".webp","JPEG":".jpg","PNG":".png"}[fmt]
        self.running=True;self.stop_event.clear();self.progress["maximum"]=len(self.paths);self.progress["value"]=0
        paths=list(self.paths)
        def job():
            reserved=set();succeeded=0;old=0;new=0
            for idx,p in enumerate(paths):
                if self.stop_event.is_set():break
                output=unique_output(dest,p.stem,ext,reserved)
                try:
                    a,b=convert_image(p,output,fmt,q,w,h)
                    succeeded+=1;old+=a;new+=b
                    delta=f"{(1-b/a)*100:+.1f}%" if a else "—"
                    status="OK"
                    name=output.name
                except Exception as e:
                    a=p.stat().st_size if p.exists() else 0;b=0;delta="—";status="Errore: "+str(e)[:55];name="—"
                self.root.after(0,lambda i=idx,a=a,b=b,di=delta,s=status,n=name,p=p:self.table.item(str(i),values=(p.name,self.size(a),self.size(b) if b else n,di,s)))
                self.root.after(0,lambda v=idx+1:self.progress.configure(value=v))
            self.root.after(0,lambda:self.done(succeeded,old,new))
        threading.Thread(target=job,daemon=True).start()
    def done(self,count,old,new):
        self.running=False
        flag="Interrotto. " if self.stop_event.is_set() else ""
        self.status.set(f"{flag}{count} immagini esportate. Dimensioni: {self.size(old)} → {self.size(new)}")

from ui_theme import apply_theme

if __name__=="__main__":
    root=tk.Tk();App(root);apply_theme(root);root.mainloop()
