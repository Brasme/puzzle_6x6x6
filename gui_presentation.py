"""GUI wrapper for the 6x6x6 Brick Presenter using Tkinter.

Run this script to launch a simple GUI where you can select bricks, set position
and rotations, place/remove bricks and see the 3D voxel view embedded.

Usage:
    python gui_presentation.py

This file depends on `presentation.py` in the same folder.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict
import random

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from presentation import CubeGrid, sample_bricks, Brick


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('6x6x6 Brick Presenter — GUI')
        self.resizable(True, True)

        # model
        self.grid = CubeGrid(size=6)
        self.bricks = sample_bricks()

        # UI layout: left controls, right canvas
        self.left = ttk.Frame(self)
        self.left.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        self.right = ttk.Frame(self)
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._build_controls()
        self._build_canvas()
        self._refresh_places_list()
        self._draw()
        # initial indicator state
        self._update_indicator()

    def _build_controls(self):
        frame = self.left

        ttk.Label(frame, text='Available bricks:').pack(anchor=tk.W)
        self.brick_list = tk.Listbox(frame, height=6, exportselection=False)
        for k in self.bricks.keys():
            self.brick_list.insert(tk.END, k)
        self.brick_list.selection_set(0)
        self.brick_list.pack(fill=tk.X)

        coords = ttk.Frame(frame)
        coords.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(coords, text='x').grid(row=0, column=0)
        ttk.Label(coords, text='y').grid(row=0, column=1)
        ttk.Label(coords, text='z').grid(row=0, column=2)
        self.spin_x = tk.Spinbox(coords, from_=0, to=5, width=4)
        self.spin_y = tk.Spinbox(coords, from_=0, to=5, width=4)
        self.spin_z = tk.Spinbox(coords, from_=0, to=5, width=4)
        self.spin_x.grid(row=1, column=0, padx=2, pady=2)
        self.spin_y.grid(row=1, column=1, padx=2, pady=2)
        self.spin_z.grid(row=1, column=2, padx=2, pady=2)

        rots = ttk.Frame(frame)
        rots.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(rots, text='rx').grid(row=0, column=0)
        ttk.Label(rots, text='ry').grid(row=0, column=1)
        ttk.Label(rots, text='rz').grid(row=0, column=2)
        self.spin_rx = tk.Spinbox(rots, from_=0, to=3, width=4)
        self.spin_ry = tk.Spinbox(rots, from_=0, to=3, width=4)
        self.spin_rz = tk.Spinbox(rots, from_=0, to=3, width=4)
        self.spin_rx.grid(row=1, column=0, padx=2, pady=2)
        self.spin_ry.grid(row=1, column=1, padx=2, pady=2)
        self.spin_rz.grid(row=1, column=2, padx=2, pady=2)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(btn_frame, text='Place', command=self.on_place).pack(fill=tk.X)
        ttk.Button(btn_frame, text='Remove selected', command=self.on_remove).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(btn_frame, text='Reset', command=self.on_reset).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(btn_frame, text='Demo', command=self.on_demo).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(btn_frame, text="Find T spaces", command=self.on_find_T).pack(fill=tk.X, pady=(4, 0))
        # option to only show placements that are adjacent to existing bricks
        self.only_adjacent_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(btn_frame, text='Only adjacent', variable=self.only_adjacent_var).pack(anchor=tk.W, pady=(4,0))
        ttk.Button(btn_frame, text='Add Random Adj T', command=self.on_add_random_adj_T).pack(fill=tk.X, pady=(4, 0))
        # Save/Load
        ttk.Button(btn_frame, text='Save...', command=self.on_save).pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_frame, text='Load...', command=self.on_load).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(btn_frame, text='Check T between', command=self.on_check_T_between).pack(fill=tk.X, pady=(6, 0))
        # visual indicator for whether a 'T' can be placed between existing bricks
        self.t_indicator = tk.Label(frame, text="T between: unknown", fg='black')
        self.t_indicator.pack(anchor=tk.W, pady=(6, 0))

        ttk.Label(frame, text='Placed bricks:').pack(anchor=tk.W, pady=(8, 0))
        self.placed_list = tk.Listbox(frame, height=8, exportselection=False)
        self.placed_list.pack(fill=tk.BOTH, expand=True)

        # move controls for selected placed brick
        move_frame = ttk.Frame(frame)
        move_frame.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(move_frame, text='Move selected:').grid(row=0, column=0, columnspan=3, sticky=tk.W)
        ttk.Button(move_frame, text='-X', width=4, command=lambda: self._move_selected((-1, 0, 0))).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(move_frame, text='+X', width=4, command=lambda: self._move_selected((1, 0, 0))).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(move_frame, text='-Y', width=4, command=lambda: self._move_selected((0, -1, 0))).grid(row=2, column=0, padx=2, pady=2)
        ttk.Button(move_frame, text='+Y', width=4, command=lambda: self._move_selected((0, 1, 0))).grid(row=2, column=1, padx=2, pady=2)
        ttk.Button(move_frame, text='-Z', width=4, command=lambda: self._move_selected((0, 0, -1))).grid(row=3, column=0, padx=2, pady=2)
        ttk.Button(move_frame, text='+Z', width=4, command=lambda: self._move_selected((0, 0, 1))).grid(row=3, column=1, padx=2, pady=2)

    def _build_canvas(self):
        # Matplotlib figure embedded
        self.fig = plt.Figure(figsize=(6, 6))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def on_place(self):
        sel = self.brick_list.curselection()
        if not sel:
            messagebox.showinfo('Info', 'Select a brick to place')
            return
        bid = self.brick_list.get(sel[0])
        try:
            x = int(self.spin_x.get())
            y = int(self.spin_y.get())
            z = int(self.spin_z.get())
            rx = int(self.spin_rx.get())
            ry = int(self.spin_ry.get())
            rz = int(self.spin_rz.get())
        except Exception:
            messagebox.showerror('Error', 'Invalid integer in inputs')
            return
        b = self.bricks[bid].rotated(rx, ry, rz).normalized()
        if not self.grid.can_place(b, (x, y, z)):
            messagebox.showwarning('Cannot place', 'Brick does not fit (out of bounds or overlap)')
            return
        try:
            pid = self.grid.place(b, (x, y, z))
            self._refresh_places_list()
            self._draw()
            self._update_indicator()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def on_remove(self):
        sel = self.placed_list.curselection()
        if not sel:
            messagebox.showinfo('Info', 'Select a placed brick to remove')
            return
        text = self.placed_list.get(sel[0])
        # format is "{pid}: {name} at (x,y,z)"
        pid = int(text.split(':', 1)[0])
        try:
            self.grid.remove(pid)
            self._refresh_places_list()
            self._draw()
            self._update_indicator()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _move_selected(self, delta):
        sel = self.placed_list.curselection()
        if not sel:
            messagebox.showinfo('Info', 'Select a placed brick to move')
            return
        text = self.placed_list.get(sel[0])
        pid = int(text.split(':', 1)[0])
        try:
            _, brick, pos = self.grid.placed[pid]
            new_pos = (pos[0] + delta[0], pos[1] + delta[1], pos[2] + delta[2])
            self.grid.move(pid, new_pos)
            self._refresh_places_list()
            self._draw()
            self._update_indicator()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _find_placements(self, bid: str, only_adjacent: bool) -> list:
        """Return list of placements (x,y,z,rx,ry,rz) for brick id `bid` that fit the current grid.

        If only_adjacent is True, only return placements that have at least one face-adjacent neighbor.
        """
        if bid not in self.bricks:
            return []
        b0 = self.bricks[bid]
        found = []
        seen = set()
        size = self.grid.size
        for rx in range(4):
            for ry in range(4):
                for rz in range(4):
                    b = b0.rotated(rx, ry, rz).normalized()
                    for x in range(size):
                        for y in range(size):
                            for z in range(size):
                                if self.grid.can_place(b, (x, y, z)):
                                    occ = tuple(sorted(((x + cx, y + cy, z + cz) for cx, cy, cz in b.cubes)))
                                    if occ in seen:
                                        continue
                                    seen.add(occ)
                                    if only_adjacent:
                                        touches = False
                                        for cx, cy, cz in b.cubes:
                                            nx, ny, nz = x + cx, y + cy, z + cz
                                            for dx, dy, dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                                                sx, sy, sz = nx + dx, ny + dy, nz + dz
                                                if 0 <= sx < size and 0 <= sy < size and 0 <= sz < size:
                                                    if self.grid.grid[sx, sy, sz] != 0:
                                                        touches = True
                                                        break
                                            if touches:
                                                break
                                        if not touches:
                                            continue
                                    found.append((x, y, z, rx, ry, rz))
        return found

    def on_find_T(self):
        """Find available placements for the 'T' brick and show them in a popup list."""
        bid = 'T'
        if bid not in self.bricks:
            messagebox.showinfo('Info', "No 'T' brick is defined")
            return
        b0 = self.bricks[bid]
        found = []
        seen = set()
        size = self.grid.size
        for rx in range(4):
            for ry in range(4):
                for rz in range(4):
                    b = b0.rotated(rx, ry, rz).normalized()
                    for x in range(size):
                        for y in range(size):
                            for z in range(size):
                                if self.grid.can_place(b, (x, y, z)):
                                    # dedupe by absolute occupied coordinates
                                    occ = tuple(sorted(((x + cx, y + cy, z + cz) for cx, cy, cz in b.cubes)))
                                    if occ in seen:
                                        continue
                                    seen.add(occ)
                                    # if only-adjacent filter is on, ensure at least one cube touches existing brick
                                    if self.only_adjacent_var.get():
                                        touches = False
                                        for cx, cy, cz in b.cubes:
                                            nx, ny, nz = x + cx, y + cy, z + cz
                                            for dx, dy, dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                                                sx, sy, sz = nx + dx, ny + dy, nz + dz
                                                if 0 <= sx < size and 0 <= sy < size and 0 <= sz < size:
                                                    if self.grid.grid[sx, sy, sz] != 0:
                                                        touches = True
                                                        break
                                            if touches:
                                                break
                                        if not touches:
                                            continue
                                    found.append((x, y, z, rx, ry, rz))

        # show results in a popup
        win = tk.Toplevel(self)
        win.title("Available 'T' placements")
        ttk.Label(win, text=f"Found {len(found)} placements for 'T'").pack(anchor=tk.W, padx=8, pady=(8, 0))
        listbox = tk.Listbox(win, width=48, height=20)
        listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        for x, y, z, rx, ry, rz in found:
            listbox.insert(tk.END, f"pos=({x},{y},{z}) rot=({rx},{ry},{rz})")
        if not found:
            listbox.insert(tk.END, "(no placements found)")
        # optional: allow double-click to place a selected placement
        def on_double(event):
            sel = listbox.curselection()
            if not sel:
                return
            item = listbox.get(sel[0])
            if item.startswith('pos='):
                # parse
                try:
                    part = item.split(' ', 1)[0]
                    coords = part[len('pos=('):-1]
                    x, y, z = [int(p) for p in coords.split(',')]
                    rotpart = item.split('rot=(')[1][:-1]
                    rx, ry, rz = [int(p) for p in rotpart.split(',')]
                    b = b0.rotated(rx, ry, rz).normalized()
                    if self.grid.can_place(b, (x, y, z)):
                        self.grid.place(b, (x, y, z))
                        self._refresh_places_list()
                        self._draw()
                        win.destroy()
                    else:
                        messagebox.showwarning('Cannot place', 'That placement is no longer valid')
                except Exception as e:
                    messagebox.showerror('Error', str(e))

        listbox.bind('<Double-1>', on_double)

    def on_add_random_adj_T(self):
        """Find all adjacent T placements and add one at random."""
        placements = self._find_placements('T', only_adjacent=True)
        if not placements:
            messagebox.showinfo('Info', 'No adjacent T placements available')
            return
        x, y, z, rx, ry, rz = random.choice(placements)
        b0 = self.bricks['T']
        b = b0.rotated(rx, ry, rz).normalized()
        try:
            self.grid.place(b, (x, y, z))
            self._refresh_places_list()
            self._draw()
            self._update_indicator()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def on_check_T_between(self):
        """Check whether a 'T' brick can be placed touching at least two distinct existing bricks."""
        if 'T' not in self.bricks:
            messagebox.showinfo('Info', "No 'T' brick defined")
            return
        possible = self.grid.can_place_somewhere(self.bricks['T'], only_adjacent=True, min_distinct_adjacent=2)
        if possible:
            messagebox.showinfo('Result', "It's possible to place a T between existing bricks.")
        else:
            messagebox.showinfo('Result', "No valid T placement found that lies between existing bricks.")

    def on_save(self):
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON files', '*.json')])
        if not path:
            return
        try:
            self.grid.save_to_file(path)
            messagebox.showinfo('Saved', f'Saved to {path}')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def on_load(self):
        path = filedialog.askopenfilename(filetypes=[('JSON files', '*.json')])
        if not path:
            return
        try:
            self.grid.load_from_file(path)
            self._refresh_places_list()
            self._draw()
            self._update_indicator()
        except Exception as e:
            messagebox.showerror('Error', str(e))

        

    def on_reset(self):
        if messagebox.askyesno('Reset', 'Clear the grid?'):
            self.grid.clear()
            self._refresh_places_list()
            self._draw()
            self._update_indicator()

    def on_demo(self):
        # place a few sample bricks if they fit
        self.grid.clear()
        b = self.bricks
        try:
            self.grid.place(b['O'], (0, 0, 0))
            self.grid.place(b['I'].rotated(0, 0, 1).normalized(), (0, 2, 0))
            self.grid.place(b['L'].rotated(0, 1, 0).normalized(), (3, 0, 0))
        except Exception:
            pass
        self._refresh_places_list()
        self._draw()
        self._update_indicator()

    def _refresh_places_list(self):
        self.placed_list.delete(0, tk.END)
        for pid, (pid2, brick, pos) in sorted(self.grid.placed.items()):
            self.placed_list.insert(tk.END, f"{pid}: {brick.name} at {pos}")

    def _draw(self):
        self.ax.clear()
        filled = self.grid.grid != 0
        if filled.any():
            unique_ids = list(sorted(set(self.grid.grid[self.grid.grid != 0].tolist())))
            cmap = plt.get_cmap('tab20')
            colors = {pid: cmap(i % 20) for i, pid in enumerate(unique_ids)}
            facecolors = [[[ (0,0,0,0) for _ in range(self.grid.size)] for __ in range(self.grid.size)] for ___ in range(self.grid.size)]
            import numpy as _np
            facearr = _np.empty(filled.shape + (4,), dtype=float)
            facearr[:] = (0, 0, 0, 0)
            for x in range(self.grid.size):
                for y in range(self.grid.size):
                    for z in range(self.grid.size):
                        pid = self.grid.grid[x, y, z]
                        if pid != 0:
                            facearr[x, y, z] = colors.get(pid, (0.5, 0.5, 0.5, 1.0))
            self.ax.voxels(filled, facecolors=facearr, edgecolor='k')
        # Always set the axes limits to show the full 6x6x6 grid
        self.ax.set_xlim(0, self.grid.size)
        self.ax.set_ylim(0, self.grid.size)
        self.ax.set_zlim(0, self.grid.size)
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.fig.tight_layout()
        self.canvas.draw()

    def _update_indicator(self):
        """Update the `t_indicator` label to show whether a 'T' can be placed between existing bricks."""
        if 'T' not in self.bricks:
            self.t_indicator.config(text="T between: no 'T' defined", fg='gray')
            return
        num = self.grid.num_left()
        if num == 0:
            self.t_indicator.config(text="Complete !!!", fg='green')
            return
        valids = self.grid.validate_placements(self.bricks['T'])
        possible = not self.grid.can_not_place_somewhere(self.bricks['T'])
        if possible:
            self.t_indicator.config(text=f"{num}:{len(valids)}: T's: YES", fg='green')
        else:
            self.t_indicator.config(text=f"{num}:{len(valids)}: T's: NO", fg='red')


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
