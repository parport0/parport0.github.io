Title: Implementing a very simple Winbond W9825G6KH SDRAM controller on a Lakritz ECP5 FPGA board
Date: 2025-01-10

This note is half-code, half-comments around this code, same as the [DDMI note](/ddmi.html).

This is the simpliest, slowest possible but yet functional
implementation of an SDR SDRAM controller, based completely
off of the chip's datasheet.

Note that the code is 0BSD licensed, meaning anyone is free to do whatever
they want with this. I hope it can be helpful as an example for people learning
FPGA programming (like I am).

Writeups do exist on the Internet about this topic, but I wished they explained more
of "how do you know that" and "how can I verify that", not only "how do you do it".

I am only learning the basics of Verilog. Please [email me](https://github.com/parport0/)
if you would like to tell me I have something wrong from the Verilog or SDRAM point of view.

### SDRAM stands for "synchronous dynamic random-access memory".

A synchronous DRAM communicates in accordance with a clock signal supplied from
the outside. A counterpart is an asynchronous DRAM, it does not take in a clock
signal, but requires all operations to follow strict timing requirements still.

A dynamic RAM is a RAM that needs to be refreshed periodically or the data
stored in it will deteriorate.  A counterpart from that perspective is SRAM;
being static, it does not need to be refreshed, but it will still lose the data
when powered off.

"SDRAM" as a term includes single data rate (SDR) and double data rate (DDR) SDRAMs.
DDR SDRAMs transfer data at twice the speed of the clock (basically both on rising
and falling edges of the clock), and SDR SDRAMs transfer data only once per clock cycle.

W9825G6KH-6 is a 4M x 4 banks x 16 SDR SDRAM in a TSOP-II-54 package, containing 32 megabytes.

### Documents

The following implementation is based on the [datasheet for Winbond W9825G6KH](https://www.winbond.com/hq/support/documentation/?__locale=en&line=/product/specialty-dram/index.html&family=/product/specialty-dram/sdram/index.html&pno=W9825G6KH&category=/.categories/resources/datasheet/).
It is a good datasheet, describes almost all you need to know if you never
worked with SDRAMs. I recommend starting with the command list truth table in section 8.

What I did not know when I started is that all modern SDRAM chips
function the same; if something in the datasheet isn't clear it is
still possible to look up "how generic SDRAM works".

Of course it could not be a coincidence; a JEDEC standard exists that covers
how SDR SDRAMs should operate and even what pinouts should be used.

(They also have standards about DDR SDRAMs, since they are the developers of those
very DDR5 and LPDDR and such standards that are used for more widely applied memories nowadays)

The standard is called [JESD21-C](https://www.jedec.org/category/technology-focus-area/memory-configurations-jesd21-c)
and its contents are available for free download for those registered (also for free)
on the JEDEC website. The contents are spread across multiple PDF downloads,
one should start with the table of contents (linked on the aforementioned page)
and then choose the appropriate pieces for further examination.

For example, the pinout for this particular part is described in JESD21-C
part "Word Wide SDRAM" (SDRAM3.11.4) (this DRAM operates in 16-bit "words", so this is
a "word wide SDRAM"), figure "8M, 16M, 32M, & 64M X 16 SDRAM IN TSOP2"
(4M words times 4 banks is 16M).

SDRAM3.11.5.1 "General SDRAM Functions" covers:

* the command list truth table
* the mode register format (although it does not cover the burst read + single write mode?)
* the power on sequence, auto-precharge, self-refresh
* etc.

So it is nice to use if the chip datasheet is not giving enough clarity.

### CAS Latency

My SDRAM model is W9825G6KH-6. It supports 133MHz/CL2 and 166MHz/CL3
"speed grades".

I couldn't find a good reference or standard clarifying where these speed grades
come from, so the table 9.5 "AC Characteristics and Operating Condition" helped.

Apparently these CL2 and CL3 markings denote the chosen, or available, "CAS Latency".

"CAS" stands for "column address strobe".

As I understand from searching around on the Internet:
when reading from a DRAM, usually, first the row part of the address is sent to the DRAM,
then the column part of the address, and finally the requested data comes back from the DRAM.

And apparently not too long ago asynchronous DRAMs were more popular, which used
strobe signals to denote "please read the row address now", "please read the column address now",
called "row address strobe" and "column address strobe", --- RAS and CAS.
"Column address strobe latency" then meant "the time inteval between sending the column address
strobe and receiving the read data".

There are no strobes in our DRAM, because it is a synchronous one, it uses a clock instead of strobes.
But the names "RAS", "CAS", and "CAS Latency" stuck from the older times.

So in our SDRAM CAS latency refers to the time in clock cycles between sending the actual
read/write commands and the data appearing on the DQ lines.

More formally, by the datasheet, this CAS Latency affects these three things:

The most important spot is not visible in the table with all the nanoseconds
but rather in the waveform 10.2 "Read Timing" again. CAS Latency set to 2 or 3 defines
if the data we read from the SDRAM will arrive 2 or 3 clock cycles after the
request has been sent.

`t_CK`, more precisely the minimum `t_CK`, is affected. The timing table says that for CL2
one clock cycle can not be faster than 7.5 nS, and for CL3 one clock cycle can
not be faster than 6 nS.  This is just another way of saying "you can set CAS
Latency to 2 only if you are running at 133 MHz or slower, and you may run at
166 MHz but only with CAS Latency of 3".

`t_HZ` and `t_AC`, which I do not care about in my implementation because I run everything
so slowly they don't matter, denote <small>the time it takes
for the DRAM to disconnect itself from the DQ lines after the raising clock edge for
the last data-out of the burst read</small> and <small>the time it takes for the DRAM
to start supplying valid data-out after the raising clock edge of the clock cycle
before the one where one would expect to read the data</small>.
Check waveform 10.2 "Read Timing" to see what this is about.

### FPGA pin configuration

For the .lpf file I again looked at the
[schematics for the board](https://github.com/machdyne/lakritz/blob/main/pcb/lakritz_v0.pdf).
The .lpf file turned out to be quite long, full of entries identical to these:

```
LOCATE COMP "dram_clk"    SITE "F16";
LOCATE COMP "dram_cas"    SITE "K16";
LOCATE COMP "dram_cke"    SITE "F15";
# ...

# SDRAM is TTL levels, not CMOS
IOBUF  PORT "dram_clk"    IO_TYPE=LVTTL33;
IOBUF  PORT "dram_cas"    IO_TYPE=LVTTL33;
IOBUF  PORT "dram_cke"    IO_TYPE=LVTTL33;
# ...
```

The first page of the datasheet says it is 3.3V, LVTTL, so not LVCMOS.

I tried to run the SDRAM at 166 MHz but failed timing,
so I am running it at my board's clock rate (48 MHz);
it makes things easier because I don't need to cross clock domains.

It is fine to run the SDRAM slower than what the speed grade says;
the 9.5 characteristics table in the datasheet does specify that the cycle time
can be as long as 1000 nS (that is just 1 MHz).
(I heard that is not a given for _DDR_ SDRAMs)

One clock cycle would be around ~21 nS (48 MHz = 20.83(3)nS).

I set the SDRAM mode to "CL2" (CAS Latency = 2) because my slow clock allows for it.

### SDRAM pins

Described in short in "5. Pin description", also useful to look at
the command list truth table in "8. Operation mode".

CLK --- clock input. Just the system clock in my case.

CKE --- clock enable, set to 1 to work with the DRAM and set to 0
for power down or suspend modes.
Looking at the command list, it seems OK to always hold CKE high
for a simple implementation. Any "low" states there relate to
"pause" states (Clock Suspend, Power Down, and Self-refresh). So I always set it to 1.

CS --- chip select, it is inverted; usually set to 0, but set to 1 when inputs
need to be ignored. Same as giving a NOP command. And we send a lot of NOPs
while waiting, for example, for a read operation to finish.

WE --- write enable, it is inverted; for read/write commands it is
1 to read, 0 to write. It also has meaning in other commands;
distinguishes "bank activate" vs "bank/all precharge" commands,
distinguishes "mode register set" vs "auto-refresh" commands.

CAS --- column address strobe, RAS --- row address strobe.
These two are just documented as "command input".
For asynchronous RAM, these pins should actually be strobed
to load in a column or a row part of the address. But for SDRAM
these pins are only used in the command decoder, and they are not
actually strobes.

LDQM --- lower data (DQ) mask, UDQM --- upper data (DQ) mask.
Usually 0; set to 1 to not write certain bits when
performing write operations, or to return Z for certain bits
when performing read operations.
Wikipedia snippet: "There is one DQM line per 8 bits".
This chip's word is 16 bits long, that's probably why
there are two DQMs in this chip.
I always set these to 0, except for the first 200us
initialization pause, where it is required to be set to 1.

BS --- bank select, for read/write, bank activation, and bank precharge.
There are four banks, hence, two BS pins.
They must also be set to 0 during Mode Register Set (reserved pins).

A --- address, used for:

* Mode Register Set to set the Mode Register contents (not DQ, interestingly)
* For bank activation: then A0-A12 specify the _row_.
* For read and write operations: A0-A8 specify the _column_, and A10 is
  special; A10 is used to specify if a read or write is performed with
  auto-precharge (= 1) or not (= 0)
* For bank precharge: A10 (only) is used to distinguish
  between single bank precharge (= 0) or all banks precharge (= 1)
  (A0-A9 and A11-A12 are not used in the precharge command).

DQ --- data, input and output, the only pins that we ever _read_
from the chip. They are just that, data, 16 bits of it.
The "DQ buffer" inside the SDRAM is the one and only one that
takes in the LDQM and UDQM signals.

### Talking to the DRAM module

```
module sdram (
	input clk_48,
	output dram_clk,
	output dram_cke,
	output reg dram_cs,
	output reg dram_we,
	output reg dram_cas,
	output reg dram_ras,
	output reg dram_ldqm,
	output reg dram_udqm,
	output reg [1:0] dram_bs,
	output reg [12:0] dram_a,
	inout [15:0] dram_dq,

	input [40:0] fifo_to_dram_data,
	output fifo_to_dram_read_flag,
	input fifo_to_dram_empty_flag,
	output [40:0] fifo_from_dram_data,
	output fifo_from_dram_write_flag,
	input fifo_from_dram_full_flag
);
    assign dram_clk = clk_48;
	assign dram_cke = 1;
```

`dram_dq` is an `inout` pin vector, because sometimes we write to it and sometimes
we read from it. Inout pins are difficult to handle; when we want to
*read* from them, we need to assign Z to them to *stop writing* to them.

A separate register, and a flag "are we reading or writing" are needed.

```
	reg dram_dq_assign = 0;
	reg [15:0] dram_dq_reg = 0;
	assign dram_dq = (dram_dq_assign) ? dram_dq_reg : {16{1'bz}};
```

I use two FIFOs for communicating with the DRAM;
one for requests ("to_dram"), and one for responses ("from_dram").
They are both of width 41 for consistency.

I assigned the bits like this in both the FIFOs:

* 40 -- 1 to write, 0 to read
* 39:38 -- address: bank
* 37:25 -- address: row
* 24:16 -- address: column
* 15:0 -- data to write (only relevant when writing)

Address is never sent from the DRAM, only to the DRAM.

A typical FIFO has an "empty" flag, a "full" flag, a "read" pin and a "write" pin, as well as "data for reading" and "data to write" lanes.

This module takes in the "reading half" of one FIFO and the "writing half" of another FIFO.

```
	// Splitting up the requests we get from the "to_dram" FIFO
	wire in_write_request = fifo_to_dram_data[40];
	wire [1:0] in_bank = fifo_to_dram_data[39:38];
	wire [12:0] in_row = fifo_to_dram_data[37:25];
	wire [8:0] in_column = fifo_to_dram_data[24:16];
	wire [15:0] in_data = fifo_to_dram_data[15:0];

	// Send the data back to the "from_dram" FIFO
	assign fifo_from_dram_data = {25'b0, dram_dq_reg};

	// These guys let the FIFOs know that an item is to be popped or to be pushed
	reg fifo_to_dram_read_flag_reg = 0;
	reg fifo_from_dram_write_flag_reg = 0;
	assign fifo_to_dram_read_flag = fifo_to_dram_read_flag_reg;
	assign fifo_from_dram_write_flag = fifo_from_dram_write_flag_reg;
```

### State machine

I will start with an overview of the states that I use, followed by an implementation and description of each.

```
	// State machine states:
	// 0 -- Initial 200uS pause
	// 1 -- Initial precharge
	// 2 -- Mode Register Set command
	// 3 -- Initial eight Auto Refresh Cycles
	// 4 -- Idle
	// 5 -- Bank Activat1e
	// 6 -- Read/Write
	// 7 -- Auto Refresh
	reg [3:0] state = 0;
```

* States 0, 1, 2, and 3 are for the initialization procedure. I go in the order the datasheet describes the procedure in.
* State 4 is the "idle" state. I send NOPs to the DRAM in that state, and I check every clock cycle if I should read or write
    something from/to the DRAM. At the same time I check if the DRAM needs to be refreshed.
* States 5 and 6 are used for the read/write operations. First an appropriate bank needs to be activated (opened),
    then the read/write command needs to be sent. In the same states I push the responses back to the FIFOs.
* State 7 is for DRAM refresh. As commonly known, DRAMs need to be "refreshed" all the time to keep the data intact.

The machine starts at state 0. Allowed states transitions:

* 0 -> 1 -> 2 -> 3 -> 4 (initialization)
* 4 -> 5 -> 6 -> 4 (reading or writing)
* 4 -> 7 -> 4 (refreshing the DRAM data)

I also need to keep count of two things.

First, oftentimes the diagrams request to wait for several clock cycles or
nanoseconds after a certain operation has been performed, to give the DRAM the
time it needs to do its things.  I stay in the same state while waiting for the
requested periods, before transitioning into the next state.
```
	reg [15:0] pause_counter = 0;
```

Second, as DRAMs need to be refreshed *periodically*, I keep a separate counter for that.

```
	reg [10:0] auto_refresh_counter = 0;
```

One final note before we go to the state machine itself; I run this logic on negedge of the clock.

I should just run it on posedge of the clock, but send a negated clock to the SDRAM. But it is done now.

The SDRAM samples all the inputs on posedge of the clock, and wants the inputs
to be stable some time before and some time after the positive clock edge.

So it is a good idea (I think) to set everything up half a clock cycle in advance to meet
the SDRAM's requirements (see the timing waveforms, chapter 10 of the datasheet).

But, same goes the other way around. When the SDRAM sends us data, it wants us to sample it on posedge of the clock.

It means that the majority of the logic in the module runs on negedge *except* for the small block
that reads from the DRAM on posedge.

For that, one more register, `dram_dq_read_reg`, is used.

```
	reg [15:0] dram_dq_read_reg = 0;

	always @(negedge clk_48) begin
```

#### Initialization procedure

This procedure is described well in the beginning of the document,
section 7 "Functional description",
but lacks timing charts or waveforms to verify yourself with.

"After power up, an initial pause of 200 uS is required".
DQM and CKE must be held high during the initial pause period
"to prevent data contention on the DQ bus".

We must not forget to set the DQM pins to 0 after this. My simple module
does not use data masks.

200 uS = 200_000 nS = 9_601 clock cycle for me, I wait a bit more.

I use the `pause_counter` here to count.

```
		if (state == 0) begin
			dram_ldqm <= 1;
			dram_udqm <= 1;

			// The NOP command
			dram_cs <= 1;

			if (pause_counter == 9610) begin // 200uS + some bits more
				state <= state + 1;
				pause_counter <= 0;
			end else begin
				pause_counter <= pause_counter + 1;
			end
		end
```

"an initial pause ... followed by a precharge of all banks using the precharge command".

It is not clear, but from the diagram 11.11 "Auto Refresh Cycle" I take that `t_RP`
(Precharge to Active Command Period) must pass after the precharge command.

15 nS = 1 clock cycle, means no NOP cycles are needed here *for me*, but *you* might need them.
All it affects is that I don't have to use a `pause_counter` in this state like in state 0.

```
		if (state == 1) begin
			// All Banks Precharge command
			dram_a[10] <= 1;
			dram_ras <= 0;
			dram_cas <= 1;
			dram_we <= 0;
			dram_cs <= 0;

			// Don't forget to unset DQM to allow read/write
			// after the initial pause
			dram_ldqm <= 0;
			dram_udqm <= 0;

			// Move on to the next state, no wait needed
			state <= state + 1;
			pause_counter <= 0;
		end
```

"After initial power up, the Mode Register Set Command must be issued for proper device operation".

Diagram 10.4 "Mode Register Set Cycle" says what to assign and to what pins
(it is only described in the diagram).

What I set in the mode register:

I use burst length 1 for simplicity.
I could use a longer burst length. That would give me 2, 4, or 8
words per read/write operation instead of just 1.

It seems to be possible to only do reads in burst mode, but still
do writes in single mode, togglable with `A[9]`.

Interleaved addressing mode is not discussed in much detail
in the datasheet. I think it is only relevant when burst length
is more than 1? I am not using it.

Timing-wise:

"A new command may be issued following the mode register set command once a delay equal to `t_RSC` has elapsed".
`t_RSC` is directly listed as 2 clock cycles in the timings table.

The same diagram for Mode Register Set shows that these 2 clock cycles can be
interpreted as "one clock cycle of sending the command, and one clock cycle of
waiting".

```
		if (state == 2) begin
			if (pause_counter == 0) begin
				// Mode Register Set
				dram_ras <= 0;
				dram_cas <= 0;
				dram_we <= 0;
				dram_cs <= 0;
				dram_a[2:0] <= 3'b000; // burst length = 1
				dram_a[3] <= 0; // sequential, not interleaved
				dram_a[6:4] <= 3'b010; // CAS latency = 2
				dram_a[8:7] <= 2'b00; // reserved
				dram_a[9] <= 0; // burst read, burst write mode, doesn't matter
				dram_a[12:10] <= 3'b000; // reserved
				dram_bs <= 2'b00; // reserved
			end else begin
				// The NOP command
				dram_cs <= 1;
			end

			if (pause_counter == 1) begin // t_RSC
				state <= state + 1;
				pause_counter <= 0;
			end else begin
				pause_counter <= pause_counter + 1;
			end
		end
```

"An additional eight Auto Refresh cycles (CBR) are also required before or after programming
the Mode Register to ensure proper subsequent operation."

I use the diagram 11.11 "Auto Refresh Cycle" again.

Eight commands that are `t_RC` (60 nS = 3 clock cycles _for me_) apart.

I split the pause_counter in two parts here.

```
		if (state == 3) begin
			// pause_counter[7:4] counts the "8 refresh cycles" part
			// pause_counter[3:0] counts the "3 clock cycles apart" part
			if (pause_counter[3:0] == 0) begin
				// Auto Refresh command
				dram_ras <= 0;
				dram_cas <= 0;
				dram_we <= 1;
				dram_cs <= 0;
			end else begin
				// The NOP command
				dram_cs <= 1;
			end

			// 0110 = 6 because it is only incremented when a cycle is done and
			// the stop condition is, the 6 is ready to be incremented to 7.
			// 0010 = 2 because it goes 0-1-2-0-1-2.
			// I am sorry for this confusing counting. Simulate your designs!
			if (pause_counter[7:0] == 8'b0110_0010) begin // 8 times 3
				state <= state + 1;
				pause_counter <= 0;
			end else if (pause_counter[3:0] == 2) begin
				pause_counter[3:0] <= 0;
				pause_counter[7:4] <= pause_counter[7:4] + 1;
			end else begin
				pause_counter[3:0] <= pause_counter[3:0] + 1;
			end
		end
```

Initialization done.

### Operation

#### Idle state

Keep checking if a new request came in the "to_dram" FIFO, but only if the
"from_dram" FIFO isn't full, so that there is space to place the response in.

This is also the state where the `auto_refresh_counter` is checked to decide
if we want to do some reading/writing or if we want to refresh the DRAM instead.

```
		if (state == 4) begin
			// The NOP command
			dram_cs <= 1;

			// Jump into the Auto-refresh state, discussed below
			if (auto_refresh_counter > 350) begin
				state <= 7;
				pause_counter <= 0;

			// A read or write request arrived,
			// and there is space in the output FIFO for us to write to
			end else if (!fifo_to_dram_empty_flag && !fifo_from_dram_full_flag) begin
				state <= state + 1;
				pause_counter <= 0;
			end

			// Clean these up from reading/writing (state 6),
			// we push to the output FIFO and pop from the input FIFO there,
			// so stop pushing / popping.
			fifo_from_dram_write_flag_reg = 0;
			fifo_to_dram_read_flag_reg = 0;
		end
```

#### Auto-Refresh

The DRAM needs to be allocated some time to re-apply electricity
to the internal capacitors to store the bits.
That's what the Auto-Refresh cycles do.

The characteristics table states "Refresh Time (8K Refresh Cycles)"
is 64 mS. The document does not clarify that, but it apparently means
that 8192 refresh cycles are needed every 64 mS (3047619 clock cycles)
They specify 8192 because that's 2^13 = number of rows in every bank!
(row is specified with pins A0-A12, that's 13 pins...)

This does not really mean that an auto-refresh is needed every 372
cycles, but that is one way to implement it.
What matters is that every cell can hold its charge for 64 mS,
and that there are 8192 rows that all need recharging.

I am doing it the simple 372-cycle way though. As could be seen in state 4,
the jump to this Auto-Refresh state is done when 350 cycles have passed
since the last Auto-Refresh (just something a bit smaller than 372).

Requirements from the datasheet:

* All banks must be closed before Auto-refresh (no banks can be open, so from
    our point of view it roughly means that all read/write procedures must be finished).
* Before giving an autorefresh command after the precharge command, one must
    wait `t_RP` (15 nS = 1 clock cycle for me, so *I* don't need to keep a counter between
    "when was the last bank closed" and "when can we start an auto-refresh cycle").
* Before giving a command after auto-refresh, one must wait t_RC (60 nS = 3 clock cycles for me;
    I spend 2 clock cycles in NOPs after sending an Auto-Refresh command for this reason).

That's what I understand from the 11.11 timing diagram at least.

One only needs to run "an auto-refresh cycle" without specifying
which row to refresh; the SDRAM remembers which row needs to be
refreshed on a given cycle.

```
		if (state == 7) begin
			if (pause_counter == 0) begin
				// The Auto-refresh command
				dram_ras <= 0;
				dram_cas <= 0;
				dram_we <= 1;
				dram_cs <= 0;
			end else begin
				// The NOP command
				dram_cs <= 1;
			end

			if (pause_counter == 2) begin // t_RC
				state <= 4;
				pause_counter <= 0;
			end else begin
				pause_counter <= pause_counter + 1;
			end
		end
```

Outside of all the states, I need to update the `auto_refresh_counter`.

```
		// On every clock cycle, increase the Auto-refresh counter
		auto_refresh_counter <= (state == 7 && pause_counter == 0) ? 0 : auto_refresh_counter + 1;
```

#### Bank activate

"The Bank Activate command must be applied before any Read or Write operation can be executed".

Reading and writing follows the sequence: Bank Activate -> Read/Write -> Bank Precharge.

Bank Activate "opens" a bank. Bank Precharge acts as "closing" a bank.
There are four banks, for some reason they must be "opened" before use.

When a bank is "opened", it is "opened" at a certain *row* as well.
Reading or writing to a different row in the same bank requires
the bank to be precharged and activated again.

It is possible to have more than one bank open at the same time!
When reading or writing, the bank which is to be used for reading
or writing is specified again.
This allows for good optimizations that I do _not_ do here.

A lot of read/write operations can be done between activating and precharging a bank.
Since my implementation is the simpliest and the slowest one, I activate and close
a bank for every word I read.

Some requirements from 7.3 "Bank Activate Command":

* "The delay from when the Bank Activate command
    is applied to when the first read or write operation can begin must not be
    less than the RAS to CAS delay time (`t_RCD`)".

    This delay is also named "Active to Read/Write Command Delay Time" in the table.
    It is 15 nS, so 1 clock cycle *for me*, means I don't need to keep a counter for it.

* The minimum time between successive Bank Activate commands:
    to the *same* bank it is `t_RC` (60 nS, 3 clock cycles for me),
    between different banks it is `t_RRD` (2 clock cycles).

    I am implementing the controller a very alow and a very simple way,
    so I am already spending more than 3 clock cycles between successive
    bank activations at least because I spend some time jumping between
    the states in my state machine.
    So I don't keep any counters for these intervals, but you might need to.

* The minimum time between precharging a bank and activating it again
    is `t_RP` (15 nS = 1 clock cycle for me, so I don't need a counter for it,
    but you might need one).

* The minimum and maximum time a bank can be active for is specified by `t_RAS`
    (min: 42 nS = 3 clock cycles for me; max: 100000 nS = a lot of clock cycles;
    I always spend more than 3 clock cycles on opening a bank and doing a read/write
    combined, so I keep no counter, but you might need to).

Basically, because of how slow my clock is, and how I only use one bank at a time,
I am never hitting these constraints. But you should be mindful of them if your clock
is faster.

In general, I use timing diagrams 11.9 "Auto-precharge Read" and 11.10 "Auto-precharge Write",
because (spoiler alert) I use Auto-precharge to automatically close banks (more on that later).

```
		if (state == 5) begin
			// Bank Activate
			dram_ras <= 0;
			dram_cas <= 1;
			dram_we <= 1;
			dram_bs[1:0] <= in_bank;
			dram_a[12:0] <= in_row;
			dram_cs <= 0;

			state <= state + 1;
			pause_counter <= 0;
		end
```

#### Read / Write

"After a bank has been activated, a read or write cycle can be followed".

First, on Auto-precharge:

Once a bank has been activated it must be *precharged*, or "closed",
before another Bank Activate command can be issued to the same bank
(so before reading from a different row, for example).

Alternatively Auto-Precharge can be used. Auto-Precharge does Bank Precharge
by itself somewhere near the end of a read/write operation. See 7.14 "Auto-precharge Command".

* For read operations:
    "the active bank will begin to precharge automatically before all
    burst read cycles have been completed" -- CAS Latency clocks prior
* For write operations:
    "The SDRAM automatically enters the precharge operation two clock
    delays from the last burst write cycle."

I already always to open -> read/write -> close for every word.
So use Auto-Precharge to "close" automatically, without the need for
a separate state and a separate command.

Timing constraints from the datasheet:

By diagrams 11.9 "Auto-precharge Read" and 11.10 "Auto-precharge Write"
having `max(t_RC, t_RAS + t_RP)`
between successive _bank activation_ operations should be fine.
In my case `max(t_RC, t_RAS + t_RP)` = `max(60nS, 57nS)` = 60nS = 3 clock cycles.

If my clock had been faster, I would have had to wait for these 60nS, minus
`t_RCD` that I had already spent in the Bank Activate state.

But my clock is so slow that this aligns perfectly. I spent one clock cycle
between Bank Activate and the Read/Write command. After the Read command,
I have to wait for CAS Latency amount of clock cycles to have the data appear
on the `DQ` lines. My CAS Latency is, again, 2.

Anyway, what I do here is: emit the Read/Write command with Auto-precharge,
wait for 2 clock cycles *always*, grab the data from the `DQ` lines if it was
a read operation, flush the FIFOs, and then go back to the Idle state.

```
		if (state == 6) begin
			if (pause_counter == 0) begin
				// Read / Write commands
				dram_a[10] <= 1; // With auto-precharge
				dram_ras <= 1;
				dram_cas <= 0;
				dram_we <= ~in_write_request; // WE is negated!
				dram_bs[1:0] <= in_bank;
				dram_a[8:0] <= in_column;

				// Assign our data to the DQ lines if we are writing.
				if (in_write_request) dram_dq_reg <= in_data;
				dram_dq_assign <= in_write_request;

				dram_cs <= 0;
			end else begin
				// The NOP command
				dram_cs <= 1;

				// Let DQ float again
				// DQ _must_ be assigned to 'Z'
				// for us to be able to read anything
				dram_dq_assign <= 0;
			end

			// Wait for t_RC - t_RCD or for the CAS latency.
			// In our case the CAS latency is longer because of
			// how slow the clock is.
			// Writing could be done faster, but it is simplier
			// to have one state handle reading and writing.
			if (pause_counter == 3) begin
				state <= 4;
				pause_counter <= 0;

				// Read, if we were reading.
				// dram_dq_read_reg is populated at posedge down below.
				dram_dq_reg <= dram_dq_read_reg;

				// Finally, flush the FIFOs
				fifo_from_dram_write_flag_reg = 1;
				fifo_to_dram_read_flag_reg = 1;
			end else begin
				pause_counter <= pause_counter + 1;
			end
		end
	end
```

#### Reading continued

This is the block that actually reads data from the DQ lines.

As I mentioned at the very top, all writes to the DRAM are done at negedge,
but reads from the DRAM must be done at *posedge*.

This is the only thing we ever read from the DRAM.

```
	always @(posedge clk_48) begin
		if (state == 6) begin
			if (pause_counter == 3) begin
				// Read, if we were reading
				if (~in_write_request) dram_dq_read_reg <= dram_dq;
			end
		end
	end
endmodule
```

### Testing

I simulated this design with iverilog first and compared it with the example waveforms.

On hardware I ran a simple test with "FIFOs" of depth 1 to check if the data is
written and read back correctly. I caught some bugs this way, for example not
inverting the WE pin and leaving DQM pins high.

A snippet of my top module for testing on hardware:

```
	// 0: writing to the dram
	// 1: reading the dram's OK response from the fifo
	// 2: reading from the dram
	// 3: reading the dram's data response from the fifo
	// 4: waiting state
	// 5: finished
	reg [2:0] state = 0;
	reg [23:0] address_to_rw = 0;
	reg [15:0] errors = 0;

	reg [43:0] counter = 0;

	// Blinky to show the FPGA is up
	assign LED = (state == 5) ? 1 : ((state == 4) ? counter[26] : ((state == 3) ? address_to_rw[21] : 0));

	// Display the DRAM test errors on a segment display
	assign segment_display_numbers = (state == 4) ? counter[31:24] : (errors[15:8] | errors[7:0]);

	always @(posedge CLK_48) begin
		if (state == 0) begin  // Write a word of test data to the DRAM
			responses_fifo_read_reg <= 0;
			if (!requests_fifo_full) begin
				requests_fifo_data_reg <= {1'b1, // write
					address_to_rw, // bank -- 2 bits + address -- 13 + 9 bits
					address_to_rw[15:0]}; // data to write -- 16 bits
				requests_fifo_write_reg <= 1;
				state <= 1;
			end else begin
				requests_fifo_write_reg <= 0;
			end
		end

		if (state == 1) begin  // Get a "the data was written" response from the DRAM
			requests_fifo_write_reg <= 0;
			if (responses_fifo_empty == 1'b0) begin
				responses_fifo_read_reg <= 1;
				if (address_to_rw == 24'hffffff) begin // Done writing
					address_to_rw <= 0;
					state <= 4;
				end else begin
					address_to_rw <= address_to_rw + 1; // Write the next word
					state <= 0;
				end
			end else begin
				responses_fifo_read_reg <= 0;
			end
		end

		// Wait for a while to see if the data is persisted on the DRAM
		if (state == 4) begin
			counter <= counter + 1;
			requests_fifo_write_reg <= 0;
			responses_fifo_read_reg <= 0;
			if (counter[31:28] == 4'b1111) begin
				address_to_rw <= 0;
				state <= 2;
			end
		end

		if (state == 2) begin  // Read a word from the DRAM
			responses_fifo_read_reg <= 0;
			if (!requests_fifo_full) begin
				requests_fifo_data_reg <= {1'b0, // read
					address_to_rw, // bank -- 2 bits + address -- 13 + 9 bits
					{4{4'b0000}}}; // empty, we are reading
				requests_fifo_write_reg <= 1;
				state <= 3;
			end else begin
				requests_fifo_write_reg <= 0;
			end
		end

		if (state == 3) begin  // Get the data from the DRAM FIFO
			requests_fifo_write_reg <= 0;
			if (responses_fifo_empty == 1'b0) begin
				data_reg <= responses_fifo_data[15:0];
				responses_fifo_read_reg <= 1;
				if (address_to_rw == 24'hffffff) begin  // All read out
					address_to_rw <= 0;
					state <= 5;  // State machine finished
				end else begin
					address_to_rw <= address_to_rw + 1;
					state <= 2;
				end

				// Expect to see the address written to the word
				// Accumulate all the errors into a register
				errors <= errors | (responses_fifo_data[15:0] ^ address_to_rw[15:0]);
			end else begin
				responses_fifo_read_reg <= 0;
			end
		end
	end
```
