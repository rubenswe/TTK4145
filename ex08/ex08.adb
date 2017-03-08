with Ada.Text_IO, Ada.Integer_Text_IO, Ada.Numerics.Float_Random;
use  Ada.Text_IO, Ada.Integer_Text_IO, Ada.Numerics.Float_Random;

procedure Ex08 is

   Count_Failed    : exception;    -- Exception to be raised when counting fails
   Gen             : Generator;    -- Random number generator

   protected type Transaction_Manager (N : Positive) is
      entry Finished;
      entry Wait_Until_Aborted;
      function Commit return Boolean;
      procedure Signal_Abort;
   private
      Finished_Gate_Open  : Boolean := False;
      Aborted             : Boolean := False;
      Should_Commit       : Boolean := True;
   end Transaction_Manager;
   protected body Transaction_Manager is
      entry Finished when Finished_Gate_Open or Finished'Count = N is
      begin
         ------------------------------------------
         -- PART 3: Complete the exit protocol here
         ------------------------------------------
         if Finished'Count = N - 1 then
            Finished_Gate_Open := True;
         end if;

         if Finished'Count = 0 then
            Aborted := False;
            Finished_Gate_Open := False;
         end if;
      end Finished;

      procedure Signal_Abort is
      begin
         Aborted := True;
      end Signal_Abort;

      function Commit return Boolean is
      begin
         return Should_Commit;
      end Commit;

      entry Wait_Until_Aborted when Aborted = True is
      begin
         null;
      end Wait_Until_Aborted;

   end Transaction_Manager;




   function Unreliable_Slow_Add (X : Integer) return Integer is
      Error_Rate : constant := 0.2;  -- (between 0 and 1)
      Random_Value : Float;
   begin
      -------------------------------------------
      -- PART 1: Create the transaction work here
      -------------------------------------------
      Random_Value := Random(Gen);

      if Random_Value > Error_Rate then
         delay Duration(Random_Value * 4.0);
         return X + 10;
      else
         delay Duration(Random_Value * 0.5);
         raise Count_Failed;
      end if;
   end Unreliable_Slow_Add;




   task type Transaction_Worker (Initial : Integer; Manager : access Transaction_Manager);
   task body Transaction_Worker is
      Num         : Integer   := Initial;
      Prev        : Integer   := Num;
      Round_Num   : Integer   := 0;
   begin
      Put_Line ("Worker" & Integer'Image(Initial) & " started");

      loop
         Put_Line ("Worker" & Integer'Image(Initial) & " started round" & Integer'Image(Round_Num));
         Round_Num := Round_Num + 1;

         ---------------------------------------
         -- PART 2: Do the transaction work here
         ---------------------------------------
         select
            Manager.Wait_Until_Aborted;   -- eg. X.Entry_Call;
            Num := Num + 5;
            Put_Line ("Worker" & Integer'Image(Initial) & " aborting" & Integer'Image(Num));
            Manager.Finished;
         then abort
            begin
               Num := Unreliable_Slow_Add(Num);
            exception
               when Count_Failed =>
                  Put_Line("-------------------------- Worker" & Integer'Image(Initial) & " failed");
                  Manager.Signal_Abort;
            end;
            Manager.Finished;
            Put_Line ("Worker" & Integer'Image(Initial) & " comitting" & Integer'Image(Num));
         end select;



         Prev := Num;
         delay 4.0;

      end loop;
   end Transaction_Worker;

   Manager : aliased Transaction_Manager (3);

   Worker_1 : Transaction_Worker (0, Manager'Access);
   Worker_2 : Transaction_Worker (1, Manager'Access);
   Worker_3 : Transaction_Worker (2, Manager'Access);

begin
   Reset(Gen); -- Seed the random number generator
end Ex08;
